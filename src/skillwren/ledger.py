"""Run ledger: record what a run did, then check its order rules on the trace.

    skillwren ledger start <flow-file> [--label TEXT] [--require NAME]... [--package DIR] [--dir DIR]
    skillwren ledger exec  <run> --step TEXT [--cwd DIR] [--readonly --sandbox-image IMG] [--dir DIR] -- <command> [args...]
    skillwren ledger note  <run> --step TEXT [--artifact PATH]... [--detail TEXT] [--dir DIR]
    skillwren ledger attempt <run> --step TEXT [--detail TEXT] [--dir DIR]
    skillwren ledger check <run> [--require-evidence] [--require-completeness] [--loaded DIR] [--json] [--dir DIR]
    skillwren ledger show  <run> [--dir DIR]
    skillwren ledger record-load            (PostToolUse hook on the Skill tool; event on stdin)

`<run>` is the id `start` printed, or `latest`. Records live in
DIR/<run>.jsonl (default `.skillwren/ledger`).

Design (docs/current/research/game-theory-2026-11.md):

- Commitment: `start` records the flow file's sha256 and its `order:` rules
  before any step, so the rules cannot be chosen after seeing the trace;
  `check` reports if the file changed since.
- Evidence classes: `exec` runs the command itself (no shell) and records its
  exit status and output digests: evidence the agent cannot simply assert.
  `note --artifact` records file digests (effect). A bare `note` is a
  self-report and is labelled so.
- Tamper evidence: each record carries the previous record's hash, so an
  edited, inserted, or deleted record breaks the chain on `check`. This makes
  manipulation detectable, not impossible: whoever controls the file can
  rewrite the whole chain.
- Exclusions: `never A before B` rules (SPEC 23) are committed at start too;
  a recorded A (step or attempt) before a recorded B is a violation.
- Provenance (field report 2026-11-19): `start --package DIR` records the
  enforcing package's tree digest; `check --loaded DIR` fails when the copy
  the host actually loaded differs, so instructions and enforcement cannot
  silently come from different versions. Without `--loaded`, `check` uses
  the host-load record a `record-load` hook wrote (hostload.py).
- Ex post checking suffices when evidence is verifiable (evidence games): a
  required step with no record is a violation, not an unknown.

Exit codes: start/note/show 0 on success; exec returns the command's exit
status; check 0 when every rule holds and the chain is intact, 1 otherwise;
2 for usage or environment errors.
"""
import argparse
import datetime
import hashlib
import json
import secrets
import subprocess
import sys
import time
from pathlib import Path

from .hostload import LOADS, latest_load, skill_name
from .validator.files import Document, looks_like_fragment
from .validator import refs
from .validator.ordering import matches

DEFAULT_DIR = Path(".skillwren") / "ledger"
TAIL = 2000


class LedgerError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seal(record, prev):
    body = dict(record, prev=prev)
    body.pop("hash", None)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["hash"] = _digest_bytes(((prev or "") + canonical).encode("utf-8"))
    return body


def run_path(directory, run):
    directory = Path(directory)
    if run == "latest":
        runs = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not runs:
            raise LedgerError(f"no runs in {directory}")
        return runs[-1]
    path = directory / f"{run}.jsonl"
    if not path.is_file():
        raise LedgerError(f"no run {run!r} in {directory}")
    return path


def load(path):
    records = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise LedgerError(f"{path}:{number}: not JSON ({error.msg})")
    if not records or records[0].get("type") != "start":
        raise LedgerError(f"{path}: first record is not a start record")
    return records


def _append(path, record):
    records = load(path)
    sealed = _seal(dict(record, seq=len(records), time=_now()), records[-1].get("hash"))
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(sealed, sort_keys=True) + "\n")
    return sealed


def package_identity(directory):
    """{path, tree_sha256, manifest_sha256} for a skill or plugin directory.

    The tree digest covers every file (not only Markdown), so hooks and
    scripts count; a `build` artifact and its source directory agree."""
    from .compiler import tree_digest, tree_files
    root = Path(directory)
    if not root.is_dir():
        raise LedgerError(f"no package directory {root}")
    files = tree_files(root)
    if not files:
        raise LedgerError(f"package directory {root} is empty")
    manifest = root / "manifest.json"
    return {"path": str(root), "tree_sha256": tree_digest(files), "files": len(files),
            "manifest_sha256": _digest_file(manifest) if manifest.is_file() else None}


def _package_copy(flow_file, package):
    """The package's copy of flow_file, matched by the longest relative path
    the package holds that ends the flow file's path, or None."""
    from .compiler import tree_files
    flow_parts = Path(flow_file).resolve().parts
    best = None
    for name, raw in tree_files(package).items():
        parts = tuple(name.split("/"))
        if flow_parts[-len(parts):] == parts and (best is None or len(parts) > len(best[0])):
            best = (parts, raw)
    return None if best is None else best[1]


def start(flow_file, directory=DEFAULT_DIR, label=None, required=(), package=None):
    flow_file = Path(flow_file)
    if not flow_file.is_file():
        raise LedgerError(f"no flow file {flow_file}")
    fragment = looks_like_fragment(flow_file)
    doc = Document(flow_file, fragment)
    rules = [{"line": r.line, "first": r.first, "then": r.then} for r in doc.contract.order]
    exclusions = [{"line": r.line, "first": r.first, "then": r.then}
                  for r in doc.contract.exclusions]
    identity = None
    if package is not None:
        identity = package_identity(package)
        copy = _package_copy(flow_file, package)
        if copy is None:
            raise LedgerError(f"package {package} holds no copy of {flow_file.name}")
        if _digest_bytes(copy) != _digest_file(flow_file):
            raise LedgerError(f"{flow_file} differs from the package's copy in {package}:"
                              " the flow being committed to is not the one the package ships")
    run = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    head = {"type": "start", "seq": 0, "time": _now(), "run": run,
            "file": str(flow_file), "file_sha256": _digest_file(flow_file),
            "layout": "fragment" if fragment else "skill", "rules": rules,
            "label": label, "required": list(required)}
    # Optional keys are omitted when empty, so older readers and digests of
    # runs that use neither feature are unchanged.
    if exclusions:
        head["exclusions"] = exclusions
    if identity:
        name = skill_name(package)
        if name:
            identity["name"] = name
        head["package"] = identity
    record = _seal(head, None)
    path = directory / f"{run}.jsonl"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    return run, path, rules


def exec_step(path, step, argv, cwd=None):
    if not argv:
        raise LedgerError("exec needs a command after --")
    began = time.monotonic()
    try:
        proc = subprocess.run(argv, capture_output=True, cwd=cwd)
        code, out, err, failure = proc.returncode, proc.stdout, proc.stderr, None
    except OSError as error:
        code, out, err, failure = 127, b"", str(error).encode("utf-8"), str(error)
    seconds = round(time.monotonic() - began, 3)
    tail = (out + err)[-TAIL:].decode("utf-8", errors="replace")
    record = {"type": "step", "class": "evidence", "step": step, "argv": list(argv),
              "exit": code, "seconds": seconds, "stdout_sha256": _digest_bytes(out),
              "stderr_sha256": _digest_bytes(err), "output_tail": tail}
    if cwd is not None:
        record["cwd"] = str(cwd)
    if failure:
        record["error"] = failure
    _append(path, record)
    return code, out, err


def readonly_step(path, step, argv, image, workspace="."):
    """Run argv in a disposable networkless container and fail closed on writes.

    The sandbox image must be pinned by digest. A nonzero exit, any file
    change inside the workspace copy, or a missing container runtime fails
    the step; the failure is recorded, not silently dropped.
    """
    from .sandbox import run
    record = {"type": "step", "class": "evidence", "step": step,
              "argv": list(argv), "readonly": True, "image": image}
    try:
        report = run(image, workspace, argv)
    except OSError as error:
        record["error"] = f"sandbox unavailable: {error}"
        _append(path, record)
        raise LedgerError(record["error"])
    record.update({"exit": report["exit"], "changed": report["changed"],
                   "undeclared": report["undeclared"],
                   "output_tail": (report["stdout"] + report["stderr"])[-TAIL:]})
    _append(path, record)
    if not report["ok"]:
        raise LedgerError(f"readonly step failed: exit {report['exit']}, "
                          f"undeclared changes {report['undeclared']}")
    return report


def note_step(path, step, artifacts=(), detail=None):
    digests = {}
    for artifact in artifacts:
        if not Path(artifact).is_file():
            raise LedgerError(f"artifact {artifact} does not exist")
        digests[str(artifact)] = _digest_file(artifact)
    record = {"type": "step", "class": "effect" if digests else "self", "step": step}
    if digests:
        record["artifacts"] = digests
    if detail is not None:
        record["detail"] = detail
    return _append(path, record)


def attempt_step(path, step, detail=None):
    """Record a try that must not satisfy order or milestones.

    Attempts are for premature or exploratory runs: `check` ignores them,
    so recording an attempt can never clear a violation or complete a run.
    Record the step again (as exec/note) when it actually completes.
    """
    record = {"type": "attempt", "step": step}
    if detail is not None:
        record["detail"] = detail
    return _append(path, record)


def verify_chain(records):
    problems, prev = [], None
    for record in records:
        if record.get("prev") != prev:
            problems.append(f"record {record.get('seq')}: chain broken (prev does not match)")
        expected = _seal(record, record.get("prev")).get("hash")
        if record.get("hash") != expected:
            problems.append(f"record {record.get('seq')}: hash does not match its content")
        prev = record.get("hash")
    seqs = [r.get("seq") for r in records]
    if seqs != list(range(len(records))):
        problems.append("records are missing or out of order")
    return problems


def step_matches(pattern, text):
    """Rule matching for recorded steps.

    Besides statement text (`verify #deps ...`), a step named exactly as the
    rule's typed reference (`verify#deps`), optionally followed by a space and
    detail, matches it: authors copy the reference from the `order:` line.
    """
    if matches(pattern, text):
        return True
    if not refs.reference(pattern):
        return False
    reference = pattern.strip()
    step = text.strip()
    return step == reference or step.startswith(reference + " ")


def completed(event):
    return event.get("class") != "evidence" or event.get("exit") == 0


def _check_exclusions(head, records):
    """`never A before B`: a recorded A (any step or attempt, completed or
    not: a failed write still happened) before a recorded B is a violation."""
    events = [r for r in records[1:] if r.get("type") in ("step", "attempt")]
    results = []
    for rule in head.get("exclusions", []):
        earlier, violations, exercised = None, [], False
        for event in events:
            text = event.get("step", "")
            if step_matches(rule["then"], text) and event.get("type") == "step":
                exercised = True
                if earlier is not None:
                    violations.append({"seq": event["seq"], "step": text,
                                       "reason": f"excluded earlier step at {earlier}"})
            if step_matches(rule["first"], text) and earlier is None:
                earlier = event["seq"]
        results.append({"rule": f"never {rule['first']} before {rule['then']}",
                        "line": rule.get("line"), "exercised": exercised,
                        "violations": violations})
    return results


def _check_package(head, loaded, loads_file=None, before=None):
    """None when no loaded copy is known; else {recorded, loaded, match, source}.
    An explicit --loaded DIR wins; otherwise the host-load record a
    PostToolUse(Skill) hook wrote (hostload.py) for the package's skill name."""
    package = head.get("package") or {}
    recorded = package.get("tree_sha256")
    if loaded is not None:
        actual = package_identity(loaded)["tree_sha256"]
        return {"recorded": recorded, "loaded": actual, "loaded_path": str(loaded),
                "source": "--loaded", "ambiguous": False,
                "match": recorded is not None and recorded == actual}
    if not package.get("name") or loads_file is None:
        return None
    load = latest_load(loads_file, package["name"], before)
    if load is None:
        return None
    return {"recorded": recorded, "loaded": load["tree_sha256"], "loaded_path": load["path"],
            "source": "host-load record", "loaded_at": load.get("time"),
            "ambiguous": bool(load.get("ambiguous")),
            "match": recorded is not None and recorded == load["tree_sha256"]}


def check(path, require_evidence=False, loaded=None):
    records = load(path)
    head = records[0]
    report = {"run": head.get("run"), "file": head.get("file"), "integrity": verify_chain(records),
              "file_changed": None, "rules": [], "steps": len(records) - 1}
    report["exclusions"] = _check_exclusions(head, records)
    report["package"] = _check_package(head, loaded, Path(path).parent.parent / LOADS,
                                       records[-1].get("time"))
    flow_file = Path(head.get("file", ""))
    if flow_file.is_file():
        report["file_changed"] = _digest_file(flow_file) != head.get("file_sha256")
    steps = [r for r in records[1:] if r.get("type") == "step"]
    for rule in head.get("rules", []):
        satisfied, violations, exercised = [], [], False
        for event in steps:
            text = event.get("step", "")
            if step_matches(rule["then"], text) and not step_matches(rule["first"], text):
                exercised = True
                if not satisfied:
                    violations.append({"seq": event["seq"], "step": text,
                                       "reason": "earlier step not completed"})
                elif require_evidence and set(satisfied) <= {"self"}:
                    violations.append({"seq": event["seq"], "step": text,
                                       "reason": "earlier step only self-reported"})
            if step_matches(rule["first"], text) and completed(event):
                satisfied.append(event["class"])
        report["rules"].append({"rule": f"{rule['first']} before {rule['then']}",
                                "line": rule.get("line"), "exercised": exercised,
                                "satisfied_by": sorted(set(satisfied)),
                                "violations": violations})
    excluded = any(r["violations"] for r in report["exclusions"])
    report["valid"] = (not report["integrity"] and not excluded
                       and not any(r["violations"] for r in report["rules"]))
    report["ok"] = report["valid"]
    report["ordering_valid"] = not excluded and not any(
        v["reason"] == "earlier step not completed"
        for r in report["rules"] for v in r["violations"])
    report["evidence_valid"] = (not any(
        v["reason"] == "earlier step only self-reported"
        for r in report["rules"] for v in r["violations"])) if require_evidence else None
    required = head.get("required", [])
    report["missing_milestones"] = [name for name in required if not any(
        e.get("step") == name and completed(e)
        and (not require_evidence or e.get("class") != "self") for e in steps)]
    report["execution_complete"] = (
        not report["missing_milestones"] and not report["integrity"]
        if required else None)
    report["ok"] = report["ok"] and not report["missing_milestones"]
    report["package_consistent"] = (None if report["package"] is None
                                    else report["package"]["match"])
    if report["package_consistent"] is False:
        report["ok"] = False
    if not report["valid"]:
        report["completeness"] = "violations"
    elif not required:
        report["completeness"] = "unassessed"
    elif report["missing_milestones"]:
        report["completeness"] = "incomplete"
    else:
        report["completeness"] = "complete"
    report["outcome"] = ("complete" if report["completeness"] == "complete"
                         else report["completeness"])
    if report["package_consistent"] is False:
        report["outcome"] = "package-mismatch"
    return report


def _print_check(report):
    print(f"run {report['run']}: {report['steps']} steps, file {report['file']}")
    for problem in report["integrity"]:
        print(f"  integrity: {problem}")
    if report["file_changed"]:
        print("  note: the flow file changed since the run started (rules were committed at start)")
    for rule in report["rules"]:
        basis = ", ".join(rule["satisfied_by"]) or "nothing"
        state = "not exercised" if not rule["exercised"] else f"earlier step from {basis}"
        print(f"  rule (line {rule['line']}) {rule['rule']!r}: {state}")
        if rule["exercised"] and rule["satisfied_by"] == ["self"]:
            print("    warning: the earlier step was only self-reported")
        for v in rule["violations"]:
            print(f"    violation at step {v['seq']} {v['step']!r}: {v['reason']}")
    for rule in report["exclusions"]:
        state = "exercised" if rule["exercised"] else "not exercised"
        print(f"  exclusion (line {rule['line']}) {rule['rule']!r}: {state}")
        for v in rule["violations"]:
            print(f"    violation at step {v['seq']} {v['step']!r}: {v['reason']}")
    package = report["package"]
    if package is not None:
        if package["recorded"] is None:
            print(f"  package: the run recorded no package; cannot vouch for {package['loaded_path']}")
        elif not package["match"]:
            print(f"  package mismatch: run committed to {package['recorded'][:12]},"
                  f" host loaded {package['loaded'][:12]} from {package['loaded_path']}")
        else:
            print(f"  package: host-loaded copy matches ({package['loaded'][:12]})")
        if package.get("source") == "host-load record":
            print(f"    (from the host-load record of {package['loaded_path']}"
                  f" at {package.get('loaded_at')})")
        if package.get("ambiguous"):
            print("    warning: several installed copies of this skill differ; the"
                  " record assumes the host's documented precedence")
    print(f"ordering_valid={report['ordering_valid']}; execution_complete={report['execution_complete']};"
          f" completeness={report['completeness']} (valid={report['valid']})")
    for name in report["missing_milestones"]:
        print(f"  missing milestone: {name}")
    print(report["outcome"])


def show(path):
    for record in load(path):
        if record["type"] == "start":
            print(f"{record['seq']:>3} {record['time']} start {record['file']}"
                  f" ({len(record.get('rules', []))} order rules)")
            continue
        kind = record.get("class") or record["type"]
        status = f"exit {record['exit']}" if record.get("class") == "evidence" else ""
        print(f"{record['seq']:>3} {record['time']} [{kind}] {record['step']} {status}".rstrip())


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren ledger",
                                     description="Record a run's steps and check its order rules.")
    sub = parser.add_subparsers(dest="action", required=True)
    p_start = sub.add_parser("start", help="commit to a flow file's order rules and open a run")
    p_start.add_argument("flow_file")
    p_start.add_argument("--label")
    p_start.add_argument("--require", action="append", default=[], dest="required",
                         help="exact required milestone name (repeatable)")
    p_start.add_argument("--package", metavar="DIR",
                         help="the skill or plugin directory enforcing this run; records its"
                              " tree digest and refuses a flow file that differs from its copy")
    p_exec = sub.add_parser("exec", help="run a command (no shell) and record its result as evidence")
    p_exec.add_argument("run")
    p_exec.add_argument("--step", required=True)
    p_exec.add_argument("--cwd", help="run the command in this directory")
    p_exec.add_argument("--readonly", action="store_true",
                        help="run in a disposable networkless container and fail on any write")
    p_exec.add_argument("--sandbox-image",
                        help="digest-pinned image for --readonly (required with it)")
    p_note = sub.add_parser("note", help="record a step without running anything")
    p_note.add_argument("run")
    p_note.add_argument("--step", required=True)
    p_note.add_argument("--artifact", action="append", default=[])
    p_note.add_argument("--detail", help="criterion or detail; the step name still matches exactly")
    p_attempt = sub.add_parser("attempt", help="record a try that satisfies nothing")
    p_attempt.add_argument("run")
    p_attempt.add_argument("--step", required=True)
    p_attempt.add_argument("--detail", default=None)
    p_check = sub.add_parser("check", help="check the order rules against the recorded steps")
    p_check.add_argument("run")
    p_check.add_argument("--require-evidence", action="store_true")
    p_check.add_argument("--require-completeness", action="store_true",
                         help="fail when no required milestones were configured (unassessed)")
    p_check.add_argument("--loaded", metavar="DIR",
                         help="the copy the host actually loaded (e.g. a plugin cache);"
                              " fail unless it matches the package recorded at start")
    p_check.add_argument("--json", action="store_true")
    p_show = sub.add_parser("show", help="list the recorded steps")
    p_show.add_argument("run")
    sub.add_parser("record-load", help="PostToolUse(Skill) hook: record which copy of a"
                                       " skill the host loaded (reads the hook event on stdin)")
    for p in (p_start, p_exec, p_note, p_attempt, p_check, p_show):
        p.add_argument("--dir", default=str(DEFAULT_DIR))
    # The command after `--` is passed through untouched, so its own flags and
    # quoting never reach argparse.
    command = []
    if argv[:1] == ["exec"] and "--" in argv:
        cut = argv.index("--")
        argv, command = argv[:cut], argv[cut + 1:]
    args = parser.parse_args(argv)
    if args.action == "record-load":
        from .hostload import hook_main
        return hook_main()
    try:
        if args.action == "start":
            run, path, rules = start(args.flow_file, args.dir, args.label, args.required,
                                     args.package)
            if not rules:
                print("skillwren ledger: the flow file has no order rules; steps are recorded,"
                      " nothing is checked", file=sys.stderr)
            print(run)
            return 0
        path = run_path(args.dir, args.run)
        if args.action == "exec":
            if args.readonly:
                if not args.sandbox_image:
                    print("skillwren ledger: --readonly needs --sandbox-image",
                          file=sys.stderr)
                    return 2
                try:
                    readonly_step(path, args.step, command, args.sandbox_image,
                                  args.cwd or ".")
                except LedgerError as error:
                    print(f"skillwren ledger: {error}", file=sys.stderr)
                    return 1
                print(f"recorded readonly step {args.step}")
                return 0
            code, out, err = exec_step(path, args.step, command, args.cwd)
            sys.stdout.buffer.write(out)
            sys.stderr.buffer.write(err)
            return code
        if args.action == "note":
            record = note_step(path, args.step, args.artifact, args.detail)
            print(f"recorded step {record['seq']} as {record['class']}")
            return 0
        if args.action == "attempt":
            record = attempt_step(path, args.step, args.detail)
            print(f"recorded attempt {record['seq']}; satisfies nothing")
            return 0
        if args.action == "check":
            report = check(path, args.require_evidence, args.loaded)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                _print_check(report)
            if args.require_completeness and report["completeness"] == "unassessed":
                if not args.json:
                    print("completeness unassessed: rerun with explicit --require milestones")
                return 1
            return 0 if report["ok"] else 1
        show(path)
        return 0
    except (LedgerError, OSError) as error:
        print(f"skillwren ledger: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
