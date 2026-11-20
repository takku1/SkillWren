"""Enforcement coverage: what kind of guarantee backs each rule, gate and effect of a skill.

    skillwren coverage FILE... [--complete] [--policy POLICY.json] [--fidelity SCORE.json] [--json]

Tiers, strongest first:
- enforced: a trusted host blocks the violation, given the deployment assumption that the
  agent reaches the protected target only through the guard (declared, not demonstrated). An order or exclusion rule whose two steps
  are guard operations of a policy bound to this flow (the guard's own test), a write that
  can only happen through a guard operation, and a gate or command that is the earlier step
  of an enforced rule (a prerequisite the protected write cannot skip).
- recorded: not blocked, but observable outside the model, so `ledger check` can detect a
  violation after the run: a rule whose earlier step leaves a command result, a user
  decision or an artifact, and gates resting on evidence or a user decision.
- instructed: rests on the model's own judgment; nothing outside the model sees it.
- unverifiable: the rule cannot be checked as written (its earlier step matches nothing).

Blocking enforces safety (something must not happen, or must not happen before something
else); it cannot make an agent do something eventually. A required step is enforced only
as a prerequisite of a protected action, which is why gates are enforced only that way.
With `--fidelity`, each requirement of a fidelity-benchmark score is given the tier of the
skill element its preserving quote sits in (prose outside the logic is instructed).
"""
import argparse
import json
from pathlib import Path
import sys

from .validator.evidence import classify
from .validator.files import Workspace, anchor_classes
from .validator.ordering import matches
from .validator.refs import reference, statement_id

TIERS = ("enforced", "recorded", "instructed", "unverifiable")
ASSUMPTION = ("the agent reaches the protected target only through the guard "
              "(host isolation; not shown by the policy)")


def _op(text):
    sid = statement_id(text)
    return f"{sid[0]}#{sid[1]}" if sid else None


def _ref(pattern):
    typed = reference(pattern)
    return f"{typed[0]}#{typed[1]}" if typed else None


def _bound(policy, path):
    flow = (policy or {}).get("workflow", {}).get("flow")
    try:
        return bool(flow) and Path(flow).resolve() == Path(path).resolve()
    except OSError:
        return False


def analyze(path, fragment=True, policy=None):
    """Coverage rows for one file: dicts with line, kind, text, tier and why."""
    workspace = Workspace()
    doc = workspace.document(path, fragment)
    ops = (policy or {}).get("operations", {})
    bound = _bound(policy, path)
    rows, prerequisites = [], {}

    steps = [(node, cls) for root in doc.trees.values() for node, cls in classify(root)["steps"]]

    def rule_row(rule, classes, kind):
        first, then = _ref(rule.first), _ref(rule.then)
        guarded = bound and first in ops and then in ops and (kind == "exclusion" or "target" in ops[then])
        if guarded:
            prerequisites.setdefault(first, []).append(rule.text)
            return "enforced", f"guard operations {first} and {then}, policy bound to this flow"
        if not classes:
            return "unverifiable", f"no statement matches {rule.first!r}"
        outside = sorted(set(classes) - {"self"})
        if outside:
            why = f"earlier step leaves {', '.join(outside)}; `ledger check` detects a violation after the run"
            if policy is not None and not bound:
                why += " (policy not bound to this flow)"
            return "recorded", why
        return "instructed", "earlier step is the model's own judgment (W15)"

    for rule, classes in anchor_classes(doc, workspace):
        tier, why = rule_row(rule, classes, "order")
        rows.append({"line": rule.line, "kind": "order rule", "text": rule.text, "tier": tier, "why": why})
    for rule in doc.contract.exclusions:
        classes = sorted({cls for node, cls in steps if matches(rule.first, node.text)})
        tier, why = rule_row(rule, classes, "exclusion")
        rows.append({"line": rule.line, "kind": "exclusion rule", "text": rule.text, "tier": tier, "why": why})

    for node, cls in steps:
        op = _op(node.text)
        if node.kind == "gate" or (node.kind == "action" and node.data == "exec"):
            kind = "gate" if node.kind == "gate" else "command"
            if op in prerequisites:
                tier, why = "enforced", f"prerequisite of enforced {'; '.join(prerequisites[op])}"
            elif cls in ("evidence", "user"):
                tier, why = "recorded", ("a command result backs it" if cls == "evidence"
                                         else "a user decision backs it")
            else:
                tier, why = "instructed", "the model's own judgment"
        elif node.kind == "action" and node.data in ("write", "save"):
            kind = "write"
            if bound and op in ops and "target" in ops[op]:
                tier, why = "enforced", f"guard operation {op} of the policy bound to this flow (pinned verifier, exact bytes)"
            elif op in ops and "target" in ops[op]:
                tier, why = "instructed", f"policy names {op} but is not bound to this flow"
            else:
                tier, why = "instructed", "not mediated: nothing outside the model blocks or records it"
        else:
            continue
        rows.append({"line": node.line, "kind": kind, "text": node.text, "tier": tier, "why": why})
    for row in rows:
        if row["tier"] == "enforced":
            # Declared, not demonstrated: the policy alone cannot show that the agent has no
            # other way to the target (SPEC 22, 24: host isolation).
            row["assumes"] = ASSUMPTION
    rows.sort(key=lambda r: r["line"])
    return rows


def requirement_tiers(path, rows, score):
    """Tier per fidelity-benchmark requirement, via the line its preserving quote sits on."""
    text = Path(path).read_text(encoding="utf-8")
    flat = " ".join(text.split())
    starts = []  # (offset in flat text, line number) for each line
    offset = 0
    for number, line in enumerate(text.splitlines(), 1):
        words = " ".join(line.split())
        if words:
            starts.append((offset, number))
            offset += len(words) + 1
    by_line = {r["line"]: r for r in rows}
    out = []
    for req in score["requirements"]:
        if req["verdict"] != "preserved":
            out.append({"id": req["id"], "kind": req["kind"], "tier": None,
                        "why": f"not preserved ({req['verdict']})"})
            continue
        quote = " ".join(req["quote"].split())
        at = flat.find(quote)
        lines = [n for o, n in starts if at <= o < at + len(quote)] or \
                [max((n for o, n in starts if o <= at), default=0)]
        hits = [by_line[n] for n in lines if n in by_line]
        if hits:
            best = min(hits, key=lambda r: TIERS.index(r["tier"]))
            out.append({"id": req["id"], "kind": req["kind"], "tier": best["tier"],
                        "why": f"{best['kind']} line {best['line']}: {best['why']}"})
        else:
            out.append({"id": req["id"], "kind": req["kind"], "tier": "instructed",
                        "why": f"prose (line {lines[0]}), not a checked element"})
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(prog="skillwren coverage", description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+")
    parser.add_argument("--complete", action="store_true", help="complete skills (contract header), not fragments")
    parser.add_argument("--policy", help="guard policy JSON (skillwren policy); without it nothing is enforced")
    parser.add_argument("--fidelity", help="a fidelity_score.py result for the (single) file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8")) if args.policy else None
    report = {}
    for path in args.files:
        rows = analyze(path, fragment=not args.complete, policy=policy)
        entry = {"items": rows, "counts": {t: sum(r["tier"] == t for r in rows) for t in TIERS}}
        if args.fidelity:
            score = json.loads(Path(args.fidelity).read_text(encoding="utf-8"))
            reqs = requirement_tiers(path, rows, score)
            entry["requirements"] = reqs
            entry["requirement_counts"] = {t: sum(r["tier"] == t for r in reqs) for t in (*TIERS, None)}
        report[path] = entry
    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0
    for path, entry in report.items():
        for r in entry["items"]:
            print(f"{path}:{r['line']}: {r['tier']:<12} {r['kind']}: {r['text']} -- {r['why']}"
                  + (" [assumes isolation]" if r.get("assumes") else ""))
        print(f"{path}: " + ", ".join(f"{n} {t}" for t, n in entry["counts"].items()))
        if entry["counts"]["enforced"]:
            print(f"{path}: enforced assumes {ASSUMPTION}")
        for r in entry.get("requirements", []):
            print(f"  {r['id']} ({r['kind']}): {r['tier'] or 'absent'} -- {r['why']}")
        if "requirement_counts" in entry:
            c = entry["requirement_counts"]
            print(f"{path}: requirements " + ", ".join(f"{c[t]} {t}" for t in TIERS) + f", {c[None]} not preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
