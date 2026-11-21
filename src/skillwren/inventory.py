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
- reverse: every behaviour-bearing statement (ask, confirmation, abort,
  retry, write, exec, run; branches as warnings) traces to a requirement,
  or is declared compiler scaffolding, which only commands and branches
  may be. This catches invention, not just omission: an unjustified ask is
  over-asking, an unjustified write a permission expansion;
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
    """(relative name, path) of a candidate's Markdown: one file, or a skill set."""
    path = Path(path)
    if path.is_file():
        return [(path.name, path)]
    if path.is_dir():
        from .compiler import fragment_set
        return [(name, path / name) for name in fragment_set(path) if name.endswith(".md")]
    raise InventoryError(f"candidate not found: {path}")


class Statement:
    """One logic statement of a candidate, as the landing checks see it.

    `rerun_of` is the line of a gate when this statement re-runs a command inside
    that gate's `otherwise:` repair to refresh the evidence the gate checks (the
    retry idiom: `exec x as r` / `verify ... from r` / `otherwise: exec x as r; retry`)."""
    __slots__ = ("file", "line", "text", "kind", "verb", "cls", "rerun_of")

    def __init__(self, file, line, text, kind, verb, cls, rerun_of=None):
        self.file, self.line, self.text = file, line, text
        self.kind, self.verb, self.cls = kind, verb, cls
        self.rerun_of = rerun_of

    @property
    def key(self):
        return (self.file, self.line)


# Statement categories that change behaviour. Each must trace to a source
# requirement (reverse traceability); only `command` and `branch` may be
# declared compiler scaffolding, and then they are reported.
BEHAVIOUR_FAILURE = {
    "decision": "over-asking or permission restriction",
    "termination": "invented abort",
    "loop": "invented retry",
    "effect": "permission expansion",
    "command": "permission expansion",
    "delegation": "invented delegation",
    "branch": "control-flow distortion",
}
SCAFFOLD_OK = ("command", "branch")


def behaviour(statement):
    kind, verb = statement.kind, statement.verb
    if kind == "action":
        return {"ask": "decision", "abort": "termination", "write": "effect",
                "save": "effect", "exec": "command", "run": "delegation"}.get(verb)
    if kind == "gate" and verb == "require":
        rest = _norm(statement.text[len("require"):]).lower()
        if rest == "confirmation" or rest.startswith("user "):
            return "decision"
    if kind in ("retry", "returnto"):
        return "loop"
    if kind == "branch":
        return "branch"
    return None


LINE_REF = re.compile(r"^(?:(?P<file>[^#\s]+)#)?L(?P<line>[1-9]\d*)$")


class Candidate:
    """What the landing checks need from a candidate: text, statements, rules."""

    def __init__(self, path):
        from .validator.evidence import classify
        from .validator.files import Document, looks_like_fragment
        from .validator.flowgraph import walk
        self.text = ""
        self.statements = []
        self.rules = []        # (file, line, text)
        files = candidate_files(path)
        self.entry = "SKILL.md" if any(n == "SKILL.md" for n, _ in files) else files[0][0]
        for name, file in files:
            raw = file.read_text(encoding="utf-8-sig")
            self.text += raw + "\n"
            if "```logic" not in raw and "```contract" not in raw:
                continue
            doc = Document(file, looks_like_fragment(file))
            for root in doc.trees.values():
                classes = {id(node): cls for node, cls in classify(root)["steps"]}
                for node in walk(root):
                    if node is root or node.kind in ("label", "otherwise", "else",
                                                     "bareword", "assign", "returnblock"):
                        continue
                    cls = classes.get(id(node), "branch" if node.kind == "branch" else "self")
                    self.statements.append(Statement(name, node.line, node.text, node.kind,
                                                     node.data, cls, _rerun_gate(node)))
            if doc.contract is not None:
                for rule in (*doc.contract.order, *doc.contract.exclusions):
                    self.rules.append((name, rule.line, rule.text))
        self.flat = _norm(self.text)

    def step(self, hits):
        """The statements one anchor may name as a single step: one statement, or one
        statement plus copies of it that only re-run it inside the repair of a gate
        checking its result. Copies on the same normal path stay ambiguous ([])."""
        if len(hits) == 1:
            return hits
        if len(hits) < 2 or len({(h.file, _norm(h.text)) for h in hits}) != 1:
            return []
        originals = [h for h in hits if h.rerun_of is None]
        return hits if len(originals) == 1 else []

    def resolve(self, anchor):
        """Statements an anchor names: a line reference (`L42`, `flows/x.md#L42`)
        names one statement; a literal names every statement containing it."""
        ref = LINE_REF.match(anchor.strip())
        if ref:
            file, line = ref.group("file") or self.entry, int(ref.group("line"))
            return [s for s in self.statements if s.file == file and s.line == line]
        return [s for s in self.statements if _matches(anchor, s.text)]

    def present(self, anchor):
        if LINE_REF.match(anchor.strip()):
            return bool(self.resolve(anchor))
        return _matches(anchor, self.flat)

    def literal(self, anchor):
        """Review-map form of an anchor: line references become statement text."""
        if LINE_REF.match(anchor.strip()):
            hits = self.resolve(anchor)
            return hits[0].text if hits else anchor
        return anchor


AS_BINDING = re.compile(r"\sas\s+([A-Za-z_][\w-]*)\s*$")


def _rerun_gate(node):
    """Gate line when `node` is a command re-run inside the `otherwise:` repair of a gate
    that cites the command's result (`verify ... from <binding>`); else None."""
    from .validator.evidence import VERIFY_FROM_RE
    if node.kind != "action" or node.data != "exec":
        return None
    bound = AS_BINDING.search(node.text)
    repair = node.parent
    gate = repair.parent if repair is not None and repair.kind == "otherwise" else None
    if not bound or gate is None or gate.kind != "gate":
        return None
    cited = VERIFY_FROM_RE.search(" " + gate.text)
    return gate.line if cited and cited.group(1) == bound.group(1) else None


def _matches(anchor, text):
    return _norm(anchor) in _norm(text)


def check_landing(inventory, candidate):
    """Forward: findings for requirements that did not land, or landed wrongly."""
    findings = []
    for item in inventory["requirements"]:
        ident, kind = item["id"], item["kind"]
        anchors = item.get("lands")
        if not isinstance(anchors, list) or not anchors or not all(
                isinstance(a, str) and a.strip() for a in anchors):
            findings.append(_finding("I4", f"{kind} requirement has no landing anchors: "
                                           f"{item['text']}", ident))
            continue
        missing = [a for a in anchors if not candidate.present(a)]
        if missing:
            findings.append(_finding("I5", "anchor not found in the candidate: "
                                     + "; ".join(repr(a) for a in missing), ident))
            continue
        hits = [s for a in anchors for s in candidate.resolve(a)]
        if kind == "order":
            if not any(_matches(candidate.literal(a), rule[2])
                       for a in anchors for rule in candidate.rules):
                findings.append(_finding("I6", "order requirement is not an `order:` rule: "
                                               + item["text"], ident))
        elif kind in STATEMENT_KINDS and not hits:
            findings.append(_finding("I6", f"{kind} requirement is not on a logic statement: "
                                           + item["text"], ident))
        evidence = item.get("evidence", "none")
        if evidence in ("exec", "user", "effect") and kind != "order":
            wanted = {"exec": ("evidence",), "user": ("user",), "effect": ("effect",)}[evidence]
            # A requirement that lands on a gate is satisfied by the gate, not by
            # a neighbouring exec: a `verify` that stops citing its exec result is
            # the measured silent-loss class even when the exec still runs.
            gates = [hit for hit in hits if hit.kind == "gate"] if evidence == "exec" else []
            if not any(hit.cls in wanted for hit in (gates or hits)):
                findings.append(_finding(
                    "I7", f"source demands {evidence} evidence, but no landed statement "
                          f"records it (a `verify ... from` an exec result, an ask/confirmation, "
                          f"or a write): " + item["text"], ident))
    return findings


def check_reverse(inventory, candidate):
    """Reverse: every behaviour-bearing statement traces to a source requirement.

    A statement is justified when a requirement's anchor names it alone (a
    line reference, or a literal matching exactly one statement): an
    ambiguous literal such as `retry` justifies nothing. A literal matching a
    command and its re-runs inside the repair of the gate that checks its
    result names that one step (`Candidate.step`). Declared
    `scaffolding` entries ({"anchor", "reason"}) cover compiler plumbing,
    and only for commands and branches; they are reported, never silent."""
    findings = []
    requirements = {item["id"]: item for item in inventory["requirements"]}
    justified = {}
    for ident, item in requirements.items():
        for anchor in item.get("lands") or []:
            if not isinstance(anchor, str):
                continue
            for hit in candidate.step(candidate.resolve(anchor)):
                justified.setdefault(hit.key, set()).add(ident)
    scaffold = {}
    entries = inventory.get("scaffolding", [])
    if not isinstance(entries, list):
        raise InventoryError("scaffolding must be a list")
    for entry in entries:
        anchor = entry.get("anchor") if isinstance(entry, dict) else None
        reason = entry.get("reason") if isinstance(entry, dict) else None
        hits = candidate.resolve(anchor) if isinstance(anchor, str) and anchor.strip() else []
        group = candidate.step(hits)
        if not group or not isinstance(reason, str) or not reason.strip():
            findings.append(_finding("I13", "scaffolding entry must name exactly one statement "
                                            "(or one command and its re-runs in the repair of the "
                                            f"gate checking it) and give a reason: {entry!r}"))
            continue
        for hit in group:
            scaffold[hit.key] = reason
    for statement in candidate.statements:
        category = behaviour(statement)
        if category is None:
            continue
        where = f"{statement.file}:{statement.line}: {statement.text}"
        ids = justified.get(statement.key)
        if ids:
            if category == "decision" and not any(
                    requirements[i]["kind"] in ("decision", "input")
                    or requirements[i].get("evidence") == "user" for i in ids):
                findings.append(dict(_finding(
                    "I12", "asks the user although its requirements are not decisions, inputs, "
                           f"or user evidence ({', '.join(sorted(ids))}): {where}",
                    severity="warning"), failure="over-asking"))
            continue
        failure = BEHAVIOUR_FAILURE[category]
        if statement.key in scaffold:
            if category in SCAFFOLD_OK:
                findings.append(dict(_finding(
                    "I10", f"compiler scaffolding ({scaffold[statement.key]}): {where}",
                    severity="warning"), failure=failure))
            else:
                findings.append(dict(_finding(
                    "I9", f"scaffolding must be behaviour-neutral; this {category} statement "
                          f"needs a source requirement: {where}"), failure=failure))
            continue
        if category == "branch":
            findings.append(dict(_finding("I11", f"branch traces to no requirement: {where}",
                                          severity="warning"), failure=failure))
        else:
            findings.append(dict(_finding(
                "I9", f"{category} statement traces to no requirement ({failure}): {where}"),
                failure=failure))
    return findings


def resolved(inventory, candidate):
    """Copy of a landed inventory with line-reference anchors as statement text."""
    copy = json.loads(json.dumps(inventory))
    for item in copy["requirements"]:
        if isinstance(item.get("lands"), list):
            item["lands"] = [candidate.literal(a) for a in item["lands"]]
    return copy


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


def check_candidate(inventory, candidate):
    """Forward landing and reverse traceability against one candidate."""
    return check_landing(inventory, candidate) + check_reverse(inventory, candidate)


def check(inventory, originals, candidate_path=None, reverse=True):
    """All findings: coverage always; landing (and, by default, reverse
    traceability) when a candidate is given."""
    findings = check_coverage(inventory, originals)
    if candidate_path is not None:
        candidate = Candidate(candidate_path)
        findings += check_landing(inventory, candidate)
        if reverse:
            findings += check_reverse(inventory, candidate)
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
            landed = resolved(inventory, Candidate(args.candidate))
            review = to_review(landed, originals, Path(args.candidate).read_bytes())
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
