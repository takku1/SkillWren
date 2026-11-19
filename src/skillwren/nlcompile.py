"""`skillwren compile`: full-context natural language to a checked SkillWren skill.

    skillwren compile SOURCE [--context FILE]... --out DIR [--layout inline|fragments]
                      [--rounds N] [--no-judge] [--keep-failed DIR] -- ADAPTER ARGV...

Phases (docs/current/design/nl-compiler.md):

1. ingest     read the entry source and declared context files; digest them.
2. inventory  the adapter lists every requirement with source line spans;
              coverage is checked mechanically (every nonblank line accounted
              for) and gaps go back to the adapter.
3. lower      the adapter writes the skill files from the inventory and names,
              per requirement, the literal anchors where it landed.
4. check      `check` diagnostics, unbacked verify gates, and inventory landing
              findings (placement by kind, demanded evidence) go back to the
              adapter until clean or the round budget is spent.
5. judge      optional: the adapter compares each requirement with the
              deterministic `explain-workflow` text; dropped requirements get
              one more repair.
6. publish    a new output directory with the skill files and `audit/`
              (inventory, review map, compile manifest, explanations).

The adapter is any executable: it gets one JSON request on stdin with a
`phase` field (`inventory`, `lower`, `repair`, `judge`) and prints one JSON
object. It proposes; nothing here approves, and the manifest keeps
`semantic_equivalence_proven: false`. Exit 0 clean, 1 compiled with open
items (questions, unrepresentable requirements, judge findings, warnings),
2 failed (nothing is published to --out).
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

from . import inventory as inv
from .review import digest, read_originals, validate_review

FORMAT = "skillwren-compile-1"
LAYOUTS = ("inline", "fragments")
TIMEOUT = 900


class CompileError(ValueError):
    """The compile could not produce a valid skill. `files` holds the last
    attempt, when there was one, for `--keep-failed`."""

    def __init__(self, message, files=None):
        super().__init__(message)
        self.files = files


def call_adapter(adapter, request, log):
    proc = subprocess.run(adapter, input=json.dumps(request), text=True,
                          encoding="utf-8", capture_output=True, timeout=TIMEOUT)
    if proc.returncode != 0:
        raise CompileError(f"adapter failed in phase {request['phase']} "
                           f"(exit {proc.returncode}): {proc.stderr[-800:]}")
    try:
        reply = json.loads(proc.stdout)
    except ValueError:
        raise CompileError(f"adapter returned no JSON in phase {request['phase']}") from None
    if not isinstance(reply, dict):
        raise CompileError(f"adapter reply in phase {request['phase']} must be an object")
    log.append({"phase": request["phase"], "usage": reply.get("usage")})
    return reply


def _strings(reply, key):
    value = reply.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise CompileError(f"adapter {key!r} must be a list of strings")
    return value


def _safe_files(files):
    """Validate adapter-written files: relative POSIX paths, text, SKILL.md present."""
    if not isinstance(files, dict) or "SKILL.md" not in files:
        raise CompileError("adapter must return files including SKILL.md")
    for name, text in files.items():
        path = PurePosixPath(name)
        if (not isinstance(text, str) or path.is_absolute() or ".." in path.parts
                or "\\" in name or ":" in name or not name or name.startswith(".")
                or "audit" == path.parts[0]):
            raise CompileError(f"adapter file name not allowed: {name!r}")
    return files


def write_files(root, files):
    for name, text in files.items():
        target = Path(root) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8",
                          newline="\n")


def diagnose(root, files):
    """`check` result for the candidate set, in the `check --json` shape."""
    from .validator.evidence import unbacked_verifies
    from .validator.files import Workspace, looks_like_fragment, validate_file
    workspace = Workspace()
    result, checked = {}, 0
    for name in sorted(files):
        if not name.endswith(".md"):
            continue
        path = Path(root) / name
        text = files[name]
        if "```logic" not in text and "```contract" not in text:
            continue
        fragment = looks_like_fragment(path)
        errors, warnings = validate_file(path, fragment=fragment, workspace=workspace)
        checked += 1
        result[name] = {
            "errors": [{"line": d.line, "rule": d.rule, "message": d.msg, "fix": d.fix}
                       for d in errors],
            "warnings": [{"line": d.line, "rule": d.rule, "message": d.msg, "fix": d.fix}
                         for d in warnings],
            "unbacked_verifies": unbacked_verifies(path, fragment=fragment)}
    if not checked:
        result["SKILL.md"] = {"errors": [{"line": 0, "rule": "C1",
                                          "message": "no logic or contract block anywhere",
                                          "fix": "Write the procedure as logic blocks."}],
                              "warnings": [], "unbacked_verifies": []}
    return result


def _errors(diagnostics):
    return sum(len(entry["errors"]) for entry in diagnostics.values())


def _land(inventory, lands):
    if not isinstance(lands, dict):
        raise CompileError("adapter `lands` must map requirement ids to anchor lists")
    known = {item["id"] for item in inventory["requirements"]}
    unknown = sorted(set(lands) - known)
    if unknown:
        raise CompileError(f"adapter landed unknown requirement ids: {', '.join(unknown)}")
    landed = json.loads(json.dumps(inventory))
    for item in landed["requirements"]:
        if item["id"] in lands:
            item["lands"] = lands[item["id"]]
        else:
            item.pop("lands", None)
    return landed


def explanations(root, files):
    from .validator.files import looks_like_fragment
    from .validator.workflow import explain_workflow
    out = {}
    for name in sorted(files):
        if name.endswith(".md") and "```logic" in files[name]:
            path = Path(root) / name
            out[name] = explain_workflow(path, looks_like_fragment(path))
    return out


class Compilation:
    def __init__(self, source, contexts, adapter, layout, rounds, judge):
        self.originals = read_originals(source, contexts)
        self.adapter = adapter
        self.layout = layout
        self.rounds = rounds
        self.judge = judge
        self.log = []
        self.questions, self.assumptions = [], []
        self.sources = {name: raw.decode("utf-8-sig") for name, raw in self.originals.items()}
        self.numbered = inv.numbered(self.originals)

    def ask(self, request):
        reply = call_adapter(self.adapter, request, self.log)
        self.questions += [q for q in _strings(reply, "questions") if q not in self.questions]
        self.assumptions += [a for a in _strings(reply, "assumptions")
                             if a not in self.assumptions]
        return reply

    # phase 2
    def build_inventory(self):
        request = {"phase": "inventory", "sources": self.numbered,
                   "entry": next(iter(self.originals))}
        findings, body = [], None
        for attempt in range(self.rounds + 1):
            if attempt:
                request = {"phase": "inventory", "sources": self.numbered,
                           "entry": next(iter(self.originals)),
                           "previous": body, "findings": findings}
            reply = self.ask(request)
            body = reply.get("inventory")
            if not isinstance(body, dict):
                raise CompileError("adapter must return an `inventory` object")
            stamped = inv.stamp(body, self.originals)
            try:
                findings = inv.check_coverage(stamped, self.originals)
            except inv.InventoryError as error:
                findings = [inv._finding("I1", str(error))]
            if not any(f["severity"] == "error" for f in findings):
                return stamped, findings
        raise CompileError("inventory still incomplete after repairs: " + "; ".join(
            f["message"] for f in findings if f["severity"] == "error"))

    # phases 3-5
    def lower(self, inventory, staging):
        request = {"phase": "lower", "sources": self.numbered, "inventory": inventory,
                   "layout": self.layout}
        judged, rounds_used = None, 0
        # Judge each clean candidate, at most twice: a judged drop earns one
        # repair, and the repaired candidate is judged again so the manifest
        # reports the verdict on the published bytes, not on an earlier draft.
        judge_left = 2 if self.judge else 0
        judge_repaired = False
        while True:
            reply = self.ask(request)
            files = _safe_files(reply.get("files"))
            landed = _land(inventory, reply.get("lands", {}))
            if staging.exists():
                shutil.rmtree(staging)
            staging.mkdir(parents=True)
            write_files(staging, files)
            diagnostics = diagnose(staging, files)
            findings = inv.check_landing(landed, inv.Candidate(staging))
            unbacked = [dict(u, file=name) for name, entry in diagnostics.items()
                        for u in entry["unbacked_verifies"]]
            clean = not _errors(diagnostics) and not any(
                f["severity"] == "error" for f in findings)
            if clean and judge_left:
                judge_left -= 1
                judged = self.ask({"phase": "judge", "inventory": landed,
                                   "explanations": explanations(staging, files)})
                for key in ("dropped", "added", "changed"):
                    judged[key] = _strings(judged, key)
                if judged["dropped"] and not judge_repaired and rounds_used < self.rounds:
                    judge_repaired = True
                    findings = [inv._finding("J1", "judge: requirement dropped or weakened: "
                                             + text) for text in judged["dropped"]]
                    clean = False
            if clean:
                return files, landed, diagnostics, findings, judged, unbacked
            if rounds_used >= self.rounds:
                raise CompileError(_failure(diagnostics, findings), files)
            rounds_used += 1
            request = {"phase": "repair", "sources": self.numbered, "inventory": inventory,
                       "layout": self.layout, "files": files, "lands": reply.get("lands", {}),
                       "diagnostics": diagnostics, "findings": findings,
                       "unbacked_verifies": unbacked}


def _failure(diagnostics, findings):
    lines = [f"{name}:{e['line']}: {e['rule']}: {e['message']}"
             for name, entry in diagnostics.items() for e in entry["errors"]]
    lines += [f"{f['rule']} {f.get('id', '-')}: {f['message']}"
              for f in findings if f["severity"] == "error"]
    return "candidate still invalid after repairs:\n  " + "\n  ".join(lines)


def compile_skill(source, out, adapter, contexts=(), layout="inline", rounds=3,
                  judge=True, keep_failed=None):
    out = Path(out).resolve()
    if out.exists():
        raise CompileError(f"output already exists: {out}")
    if not out.parent.is_dir():
        raise CompileError(f"output parent does not exist: {out.parent}")
    job = Compilation(source, contexts, adapter, layout, rounds, judge)
    inventory, coverage = job.build_inventory()
    with tempfile.TemporaryDirectory(prefix="skillwren-compile-", dir=out.parent) as temp:
        staging = Path(temp) / "artifact"
        try:
            files, landed, diagnostics, findings, judged, unbacked = job.lower(
                inventory, staging)
        except CompileError as error:
            if keep_failed and error.files:
                write_files(Path(keep_failed), error.files)
            raise
        audit = staging / "audit"
        audit.mkdir()
        (audit / "inventory.json").write_text(json.dumps(landed, indent=2) + "\n",
                                              encoding="utf-8")
        for name, text in explanations(staging, files).items():
            (audit / (name.replace("/", "__") + ".explain.txt")).write_text(
                text, encoding="utf-8")
        review_status = None
        if list(files) == ["SKILL.md"]:
            candidate = (staging / "SKILL.md").read_bytes()
            review = inv.to_review(landed, job.originals, candidate)
            review_status = validate_review(job.originals, candidate, candidate, review)
            (audit / "review.json").write_text(json.dumps(review, indent=2) + "\n",
                                               encoding="utf-8")
        warnings = [dict(w, file=name) for name, entry in diagnostics.items()
                    for w in entry["warnings"]]
        open_items = (coverage + [f for f in findings if f["severity"] != "error"])
        manifest = {
            "format": FORMAT, "layout": layout,
            "sources": {name: digest(raw) for name, raw in job.originals.items()},
            "outputs": {name: digest((staging / name).read_bytes()) for name in files},
            "adapter": adapter, "calls": job.log,
            "requirements": len(landed["requirements"]),
            "non_requirements": len(landed.get("non_requirements", [])),
            "check_warnings": warnings, "unbacked_verifies": unbacked,
            "open_findings": open_items, "judge": judged,
            "questions": job.questions, "assumptions": job.assumptions,
            "review_map": review_status,
            "approved": False, "semantic_equivalence_proven": False}
        (audit / "compile-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if out.exists():
            raise CompileError(f"output already exists: {out}")
        staging.rename(out)
    return manifest


def is_open(manifest):
    judged = manifest["judge"] or {}
    return bool(manifest["questions"] or manifest["open_findings"]
                or manifest["check_warnings"] or manifest["unbacked_verifies"]
                or any(judged.get(k) for k in ("dropped", "added", "changed")))


def main(argv):
    parser = argparse.ArgumentParser(
        prog="skillwren compile",
        description="Compile a natural-language skill or intent document into a "
                    "checked SkillWren skill through a model adapter. Proposal only: "
                    "explain, review, and approve before use.",
        epilog="Give the adapter after `--` as plain words: "
               "skillwren compile SKILL.md --out out -- py -3 scripts/adapters/claude_compile.py")
    parser.add_argument("source")
    parser.add_argument("--context", action="append", default=[],
                        help="additional source file inside the source's folder (repeatable)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--layout", choices=LAYOUTS, default="inline")
    parser.add_argument("--rounds", type=int, default=3,
                        help="repair rounds per phase (default 3)")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--keep-failed", help="on failure, write the last attempt here")
    parser.add_argument("--json", action="store_true", help="print the manifest as JSON")
    adapter = []
    if "--" in argv:
        cut = argv.index("--")
        argv, adapter = argv[:cut], argv[cut + 1:]
    args = parser.parse_args(argv)
    if not adapter:
        parser.error("give the adapter after --")
    if args.rounds < 0:
        parser.error("--rounds must be zero or more")
    try:
        manifest = compile_skill(args.source, args.out, adapter, args.context, args.layout,
                                 args.rounds, not args.no_judge, args.keep_failed)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"skillwren compile: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(f"compiled {args.out}: {manifest['requirements']} requirements, "
              f"{len(manifest['outputs'])} files, {len(manifest['calls'])} adapter calls")
        for label, items in (("questions", manifest["questions"]),
                             ("assumptions", manifest["assumptions"])):
            if items:
                print(f"{label}:")
                for item in items:
                    print(f"  - {item}")
        for finding in manifest["open_findings"]:
            print(f"open {finding['rule']} {finding.get('id', '-')}: {finding['message']}")
        for warning in manifest["check_warnings"]:
            print(f"warning {warning['file']}:{warning['line']} {warning['rule']}: "
                  f"{warning['message']}")
        for gate in manifest["unbacked_verifies"]:
            print(f"unbacked verify {gate['file']}:{gate['line']}: {gate['text']}")
        judged = manifest["judge"] or {}
        for key in ("dropped", "added", "changed"):
            for text in judged.get(key, []):
                print(f"judge {key}: {text}")
        print("Not approved. Review audit/, run explain-workflow, and approve before use.")
    return 1 if is_open(manifest) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
