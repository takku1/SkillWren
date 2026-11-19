"""Requirement inventory: the compiler's accounting of a natural-language source.

An inventory lists every requirement a source states, with the source lines
it came from, and (after lowering) the literal anchors where it landed in
the SkillWren candidate. Three checks, all deterministic:

- coverage: every nonblank source line belongs to a requirement or to an
  explicit non-requirement with a reason; digests bind the inventory to the
  exact source bytes;
- landing: every requirement names anchors found in the candidate, and the
  anchor's placement fits the requirement's kind (an order requirement lands
  on an `order:` rule, a gate on a logic statement, and so on), including
  the evidence the source demanded (`exec`, `user`, `effect`);
- review: the landed inventory converts to the hash-bound `review.json`
  that `build --original --review` already validates.

None of this proves semantic equivalence. It turns silent requirement loss
into a named, line-referenced finding.

    skillwren inventory check INVENTORY --source FILE [--context FILE]...
                              [--candidate PATH] [--json]
    skillwren inventory review INVENTORY --source FILE [--context FILE]...
                               --candidate FILE --out review.json
"""
import argparse
import json
from pathlib import Path
import re
import sys

from .review import digest, read_originals

FORMAT = "skillwren-inventory-1"
KINDS = ("order", "gate", "branch", "decision", "effect", "recovery", "invariant",
         "input", "output", "step-meaning", "context", "unrepresentable")
# Kinds that must land on a logic statement (control), on an order rule, or
# anywhere in the candidate text (prose sections, contract lines).
STATEMENT_KINDS = ("gate", "branch", "decision", "effect", "recovery")
EVIDENCE = ("exec", "user", "effect", "self", "none")
ID_RE = re.compile(r"^[A-Za-z][\w.-]*$")
SPACE_RE = re.compile(r"\s+")


class InventoryError(ValueError):
    """The inventory is malformed or bound to other source bytes."""


def _norm(text):
    return SPACE_RE.sub(" ", text).strip()


def _finding(rule, message, ident=None, severity="error"):
    item = {"rule": rule, "severity": severity, "message": message}
    if ident is not None:
        item["id"] = ident
    return item


def _span(entry, lines, where):
    if not isinstance(entry, dict):
        raise InventoryError(f"{where}: source span must be an object")
    name = entry.get("file")
    if name not in lines:
        raise InventoryError(f"{where}: unknown source file {name!r}")
    span = entry.get("lines")
    if (not isinstance(span, list) or len(span) != 2
            or any(type(n) is not int for n in span)
            or not 1 <= span[0] <= span[1] <= len(lines[name])):
        raise InventoryError(f"{where}: invalid line span {span!r} in {name}")
    return name, span


def source_lines(originals):
    return {name: raw.decode("utf-8-sig").splitlines() for name, raw in originals.items()}


def numbered(originals):
    """Sources as `name:line: text` listings, the form a model sees."""
    out = {}
    for name, lines in source_lines(originals).items():
        out[name] = "\n".join(f"{i:4}| {line}" for i, line in enumerate(lines, 1))
    return out


def stamp(inventory, originals):
    """Bind an inventory body to the source bytes (format and digests)."""
    body = dict(inventory)
    body["format"] = FORMAT
    body["sources"] = {name: digest(raw) for name, raw in originals.items()}
    body.setdefault("non_requirements", [])
    return body


def check_coverage(inventory, originals):
    """Schema, digest, and line-coverage findings. Raises on a malformed
    inventory or changed sources; returns findings for gaps."""
    if not isinstance(inventory, dict) or inventory.get("format") != FORMAT:
        raise InventoryError(f"inventory must be an object with format {FORMAT!r}")
    expected = {name: digest(raw) for name, raw in originals.items()}
    if inventory.get("sources") != expected:
        raise InventoryError("sources changed or differ from the inventory's digests")
    lines = source_lines(originals)
    requirements = inventory.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise InventoryError("inventory needs a nonempty requirements list")
    covered = {name: set() for name in lines}
    seen = set()
    findings = []
    for index, item in enumerate(requirements):
        where = f"requirement {index}"
        if not isinstance(item, dict):
            raise InventoryError(f"{where} must be an object")
        ident = item.get("id")
        if not isinstance(ident, str) or not ID_RE.match(ident) or ident in seen:
            raise InventoryError(f"{where}: id must be unique and match {ID_RE.pattern}")
        seen.add(ident)
        where = f"requirement {ident}"
        if item.get("kind") not in KINDS:
            raise InventoryError(f"{where}: kind must be one of {', '.join(KINDS)}")
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise InventoryError(f"{where}: text must be nonempty")
        if item.get("evidence", "none") not in EVIDENCE:
            raise InventoryError(f"{where}: evidence must be one of {', '.join(EVIDENCE)}")
        spans = item.get("source")
        if not isinstance(spans, list) or not spans:
            raise InventoryError(f"{where}: source must list at least one span")
        for entry in spans:
            name, span = _span(entry, lines, where)
            covered[name].update(range(span[0], span[1] + 1))
        if item["kind"] == "unrepresentable":
            findings.append(_finding("I8", "kept as prose, not checkable: " + item["text"],
                                     ident, "warning"))
    others = inventory.get("non_requirements", [])
    if not isinstance(others, list):
        raise InventoryError("non_requirements must be a list")
    for index, entry in enumerate(others):
        where = f"non-requirement {index}"
        name, span = _span(entry, lines, where)
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise InventoryError(f"{where}: needs a reason")
        covered[name].update(range(span[0], span[1] + 1))
    for name, text in lines.items():
        missing = [i for i, line in enumerate(text, 1) if line.strip() and i not in covered[name]]
        if missing:
            findings.append(_finding(
                "I3", f"{name}: source lines not accounted for: {_ranges(missing)}"))
    return findings


def _ranges(numbers):
    out, start = [], None
    for i, n in enumerate(numbers):
        if start is None:
            start = n
        if i + 1 == len(numbers) or numbers[i + 1] != n + 1:
            out.append(str(start) if start == n else f"{start}-{n}")
            start = None
    return ", ".join(out)


# ---------------------------------------------------------------- candidate

def candidate_files(path):
    """Markdown files of a candidate: one file, or every .md of a skill set."""
    path = Path(path)
    if path.is_file():
        return [path]
    if path.is_dir():
        from .compiler import fragment_set
        return [path / name for name in fragment_set(path) if name.endswith(".md")]
    raise InventoryError(f"candidate not found: {path}")


class Candidate:
    """What the landing check needs from a candidate: text, statements, rules."""

    def __init__(self, path):
        from .validator.evidence import classify
        from .validator.files import Document, looks_like_fragment
        self.text = ""
        self.statements = []   # (file, line, text, kind, verb, class)
        self.rules = []        # (file, line, text)
        for file in candidate_files(path):
            raw = file.read_text(encoding="utf-8-sig")
            self.text += raw + "\n"
            if "```logic" not in raw and "```contract" not in raw:
                continue
            doc = Document(file, looks_like_fragment(file))
            for root in doc.trees.values():
                for node, cls in classify(root)["steps"]:
                    self.statements.append((file.name, node.line, node.text, node.kind,
                                            node.data, cls))
                for node in _branches(root):
                    self.statements.append((file.name, node.line, node.text, node.kind,
                                            node.data, "branch"))
            if doc.contract is not None:
                for rule in doc.contract.order:
                    self.rules.append((file.name, rule.line, rule.text))
        self.flat = _norm(self.text)


def _branches(root):
    from .validator.flowgraph import walk
    return [node for node in walk(root) if node.kind == "branch"]


def _matches(anchor, text):
    return _norm(anchor) in _norm(text)


def check_landing(inventory, candidate):
    """Findings for requirements that did not land, or landed in the wrong place."""
    findings = []
    for item in inventory["requirements"]:
        ident, kind = item["id"], item["kind"]
        anchors = item.get("lands")
        if not isinstance(anchors, list) or not anchors or not all(
                isinstance(a, str) and a.strip() for a in anchors):
            findings.append(_finding("I4", f"{kind} requirement has no landing anchors: "
                                           f"{item['text']}", ident))
            continue
        missing = [a for a in anchors if not _matches(a, candidate.flat)]
        if missing:
            findings.append(_finding("I5", "anchor not found in the candidate: "
                                     + "; ".join(repr(a) for a in missing), ident))
            continue
        hits = [s for s in candidate.statements if any(_matches(a, s[2]) for a in anchors)]
        if kind == "order":
            if not any(_matches(a, rule[2]) for a in anchors for rule in candidate.rules):
                findings.append(_finding("I6", "order requirement is not an `order:` rule: "
                                               + item["text"], ident))
        elif kind in STATEMENT_KINDS and not hits:
            findings.append(_finding("I6", f"{kind} requirement is not on a logic statement: "
                                           + item["text"], ident))
        evidence = item.get("evidence", "none")
        if evidence in ("exec", "user", "effect") and kind != "order":
            wanted = {"exec": ("evidence",), "user": ("user",), "effect": ("effect",)}[evidence]
            if not any(hit[5] in wanted for hit in hits):
                findings.append(_finding(
                    "I7", f"source demands {evidence} evidence, but no landed statement "
                          f"records it (a `verify ... from` an exec result, an ask/confirmation, "
                          f"or a write): " + item["text"], ident))
    return findings


def to_review(inventory, originals, candidate_bytes, note=None):
    """The landed inventory as a `review.json` for `build --original --review`."""
    names = list(originals)
    requirements = []
    for item in inventory["requirements"]:
        spans = item["source"]
        for index, entry in enumerate(spans):
            ident = item["id"] if len(spans) == 1 else f"{item['id']}.{index + 1}"
            record = {"id": ident, "original_lines": entry["lines"],
                      "logic_contains": item["lands"]}
            if entry["file"] != names[0]:
                record["original_file"] = entry["file"]
            requirements.append(record)
    review = {"original_sha256": digest(originals[names[0]]),
              "logic_sha256": digest(candidate_bytes),
              "review": note or "Generated from a compiler inventory; anchors are "
                                "bookkeeping, not an equivalence proof.",
              "requirements": requirements,
              "non_requirements": [
                  dict({"original_lines": e["lines"], "reason": e["reason"]},
                       **({"original_file": e["file"]} if e["file"] != names[0] else {}))
                  for e in inventory.get("non_requirements", [])]}
    if len(names) > 1:
        review["original_context_sha256"] = {n: digest(originals[n]) for n in names[1:]}
    return review


def check(inventory, originals, candidate_path=None):
    """All findings: coverage always, landing when a candidate is given."""
    findings = check_coverage(inventory, originals)
    if candidate_path is not None:
        findings += check_landing(inventory, Candidate(candidate_path))
    return findings


def summary(findings):
    errors = sum(1 for f in findings if f["severity"] == "error")
    return {"ok": errors == 0, "errors": errors, "warnings": len(findings) - errors}


# ---------------------------------------------------------------- CLI

def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except ValueError as error:
        raise InventoryError(f"{path}: not JSON: {error}") from None


def main(argv):
    parser = argparse.ArgumentParser(
        prog="skillwren inventory",
        description="Check a requirement inventory against its sources and a "
                    "candidate, or turn it into a build review map.")
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("check", "review"):
        command = sub.add_parser(name)
        command.add_argument("inventory")
        command.add_argument("--source", required=True, help="entry source file")
        command.add_argument("--context", action="append", default=[],
                             help="additional source file inside the entry's folder")
        command.add_argument("--candidate", required=(name == "review"),
                             help="candidate skill file (or skill folder for check)")
        if name == "check":
            command.add_argument("--json", action="store_true")
        else:
            command.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        originals = read_originals(args.source, args.context)
        inventory = _load(args.inventory)
        findings = check(inventory, originals, args.candidate)
        if args.action == "review":
            errors = [f for f in findings if f["severity"] == "error"]
            if errors:
                raise InventoryError("inventory has open findings:\n" + "\n".join(
                    f"  {f['rule']} {f.get('id', '-')}: {f['message']}" for f in errors))
            if not Path(args.candidate).is_file():
                raise InventoryError("review maps take a single-file candidate")
            review = to_review(inventory, originals, Path(args.candidate).read_bytes())
            out = Path(args.out)
            if out.exists():
                raise InventoryError(f"output already exists: {out}")
            out.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {out}: {len(review['requirements'])} mapped spans")
            return 0
    except (OSError, ValueError) as error:
        print(f"skillwren inventory: {error}", file=sys.stderr)
        return 2
    result = summary(findings)
    if args.json:
        print(json.dumps(dict(result, format="skillwren-inventory-check-1",
                              findings=findings), indent=2))
    else:
        for f in findings:
            print(f"{f['severity']} {f['rule']} {f.get('id', '-')}: {f['message']}")
        print("clean" if not findings else
              f"{result['errors']} errors, {result['warnings']} warnings")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
