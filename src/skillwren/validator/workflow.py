"""Deterministic workflow dump and explanation (authoring support, no model).

`dump_workflow` serializes the parsed AST to a versioned dict: every
statement keeps its source line, so any consumer can trace a claim back to
the text. Statements from source are marked explicit; analyzer-derived
facts (inferred inputs) are segregated under `inferred`, never mixed in.

`explain_workflow` renders the same structure as plain language: ordered
steps, branches, order rules, authority gates, effects, and which parts are
eligible for guard enforcement versus advisory-only. It describes meaning;
rule compliance still comes from `check`.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from .files import Document, looks_like_fragment, summarize
from .flowgraph import walk

DUMP_VERSION = 1

TYPED_ID_RE = re.compile(r"#[A-Za-z][\w-]*")
RUN_RE = re.compile(r"^run\s+(\S+)\s+from\s+(\S+)")

# Verbs a guard policy operation can bind. Anything else is advisory-only:
# the controller has no operation to attach it to.
GUARD_VERBS = ("verify", "write", "exec")


def _dump_node(node):
    item = {"line": node.line, "kind": node.kind, "text": node.text,
            "explicit": True}
    if node.data is not None:
        item["detail"] = node.data
    if node.children:
        item["children"] = [_dump_node(child) for child in node.children]
    return item


def dump_workflow(path, fragment=None):
    """Versioned AST dump with line provenance and explicit/inferred split."""
    path = Path(path)
    if fragment is None:
        fragment = looks_like_fragment(path)
    doc = Document(path, fragment)
    flows = {}
    for flow, root in doc.trees.items():
        flows[flow] = [_dump_node(child) for child in root.children]
    rules = [{"line": rule.line, "first": rule.first, "then": rule.then}
             for rule in doc.contract.order]
    declared = list(getattr(doc.contract, "inputs", None) or [])
    touches = summarize(str(path), fragment)
    inferred_inputs = sorted(
        {name for flow in touches.values() for name in flow["inputs"]}
        - set(declared))
    return {"version": DUMP_VERSION, "file": str(path), "fragment": fragment,
            "flows": flows, "order_rules": rules,
            "declared_inputs": declared,
            "inferred": {"inputs": inferred_inputs,
                         "note": "inferred from use, not declared; "
                                 "confirm before treating as requirements"},
            "touches": {flow: {"writes": facts["writes"], "runs": facts["runs"]}
                        for flow, facts in touches.items()}}


def _typed_ids(text):
    return TYPED_ID_RE.findall(text)


def _describe(node, depth):
    pad = "  " * depth
    ref = f"(line {node.line})"
    kind, text = node.kind, node.text
    if kind == "gate":
        return f"{pad}- {text!r} {ref} -- gate; failure follows its otherwise branch"
    if kind == "branch":
        return f"{pad}- {text!r} {ref} -- branch"
    if kind == "otherwise":
        return f"{pad}- otherwise {ref}"
    if kind == "action":
        return f"{pad}- {text!r} {ref}"
    if kind == "assign":
        return f"{pad}- set {text!r} {ref}"
    if kind == "returnblock":
        return f"{pad}- return {ref}"
    if kind == "returnto":
        return f"{pad}- return to {text!r} {ref}"
    if kind == "retry":
        return f"{pad}- retry {ref}"
    if kind == "label":
        return f"{pad}- label {text!r} {ref}"
    if kind == "foreach":
        return f"{pad}- for each {text!r} {ref}"
    return f"{pad}- {text!r} {ref} [{kind}]"


def _walk_render(nodes, depth, lines):
    for node in nodes:
        lines.append(_describe(node, depth))
        if node.children:
            _walk_render(node.children, depth + 1, lines)


def explain_workflow(path, fragment=None):
    """Plain-language meaning of a workflow, derived from the AST only."""
    path = Path(path)
    if fragment is None:
        fragment = looks_like_fragment(path)
    doc = Document(path, fragment)
    dump = dump_workflow(path, fragment)
    lines = [f"Workflow in {path.name}:"]
    for flow, root in doc.trees.items():
        lines.append(f"flow `{flow}`:")
        if not root.children:
            lines.append("  (no steps)")
        _walk_render(root.children, 1, lines)
    if dump["order_rules"]:
        lines.append("Ordering (must hold on every path):")
        for rule in dump["order_rules"]:
            lines.append(f"  - {rule['first']!r} before {rule['then']!r} "
                         f"(line {rule['line']})")
    else:
        lines.append("Ordering: no order rules; steps may run in any order.")
    asks = [node for root in doc.trees.values() for node in walk(root)
            if node.kind == "action" and node.data == "ask"]
    if asks:
        lines.append("Authority: human decisions are asked here:")
        for node in asks:
            lines.append(f"  - {node.text!r} (line {node.line})")
        lines.append("  SkillWren checks the ask/confirm structure, not "
                     "that a human actually decided -- approval confirms "
                     "intended meaning, not formal equivalence.")
    else:
        lines.append("Authority: no ask steps; nothing requires a human decision.")
    touches = dump["touches"]
    effected = [(flow, facts) for flow, facts in touches.items()
                if facts["writes"] or facts["runs"]]
    if effected:
        lines.append("Effects (files written or flows run):")
        for flow, facts in effected:
            for target in facts["writes"]:
                lines.append(f"  - flow `{flow}` writes {target}")
            for target in facts["runs"]:
                lines.append(f"  - flow `{flow}` runs {target}")
    else:
        lines.append("Effects: none declared; the workflow changes nothing.")
    eligible, advisory = [], []
    for flow, root in doc.trees.items():
        for node in walk(root):
            if node.kind not in ("action", "gate"):
                continue
            if node.data not in GUARD_VERBS:
                continue
            (eligible if _typed_ids(node.text) else advisory).append(node)
    lines.append("Enforcement:")
    for node in eligible:
        lines.append(f"  - {node.text!r} (line {node.line}) is addressable by "
                     "order rules and eligible for guard enforcement, but only "
                     "if the guard policy defines that operation.")
    for node in advisory:
        lines.append(f"  - {node.text!r} (line {node.line}) is advisory-only: "
                     "no stable ID, so order rules match it by prose text and "
                     "the guard cannot bind it.")
    if not eligible and not advisory:
        lines.append("  No guard verbs present; nothing here can be enforced.")
    calls = _calls(doc)
    if calls:
        lines.append("Calls (cross-file runs):")
        lines.extend(f"  - {call}" for call in calls)
    else:
        lines.append("Calls: no cross-file runs; the meaning above is complete.")
    lines.append("What this text cannot show: the prose meaning of untyped "
                 "steps is not machine-checked, so rewording can silently "
                 "change intent; correlated branch conditions are not "
                 "recognized; approval here is not a guard policy and grants "
                 "no capabilities. Run `check` for rule compliance. "
                 "Deterministic from the AST: no model paraphrased this text.")
    return "\n".join(lines) + "\n"


def _calls(doc):
    """One line per cross-file run: target, resolved file, callee flows."""
    from .files import Workspace
    workspace = Workspace()
    calls = []
    for flow, root in doc.trees.items():
        for node in walk(root):
            if node.kind != "action" or node.data != "run":
                continue
            match = RUN_RE.match(node.text)
            if not match:
                calls.append(f"flow `{flow}` runs an unparsable target "
                             f"{node.text!r} (line {node.line}) -- meaning unknown")
                continue
            target, rel = match.groups()
            resolved = workspace.resolve_path(doc, rel)
            if resolved is None:
                calls.append(f"flow `{flow}` runs `{target}` from {rel} "
                             f"(line {node.line}) -- UNRESOLVED, unverified "
                             f"boundary: the callee meaning is unknown")
                continue
            try:
                callee = workspace.document(resolved)
                names = ", ".join(sorted(callee.trees)) or "(no flows)"
            except (OSError, ValueError):
                names = "UNREADABLE"
            calls.append(f"flow `{flow}` runs `{target}` from {rel} "
                         f"(line {node.line}) -- target file flows: {names}")
    return calls


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren explain-workflow",
                                     description="Describe a workflow's meaning "
                                                 "deterministically from its AST.")
    parser.add_argument("file")
    parser.add_argument("--fragment", action="store_true")
    parser.add_argument("--json", action="store_true",
                        help="print the versioned AST dump instead of prose")
    args = parser.parse_args(argv)
    try:
        if args.json:
            print(json.dumps(dump_workflow(args.file, args.fragment), indent=2))
        else:
            print(explain_workflow(args.file, args.fragment), end="")
        return 0
    except (OSError, ValueError) as error:
        print(f"skillwren explain-workflow: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
