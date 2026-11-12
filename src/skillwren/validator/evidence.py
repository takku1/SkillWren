"""Evidence classes and branch controllers (0.7).

Game-theoretic reading (docs/current/research/game-theory-2026-11.md): a step
the principal cannot observe cannot be contracted on, and a self-report is
cheap talk. Each statement is graded by what an outside verifier could see:

- evidence:  an `exec` (exit status, output), or a gate citing an `exec`/`read`
             result with `verify ... from <name>`
- effect:    a `write`/`save` (the artifact exists afterwards)
- user:      a decision ask or confirmation (the user moved)
- delegated: a `run` (graded by what the callee does)
- self:      everything else: the model's own judgment

Branch conditions are labelled by who decides them: `user` (tests an answer
to an input ask), `evidence` (tests an exec/read result), or `model`.
"""
import re

from .flowgraph import walk
from .syntax import as_target, norm

EVIDENCE_VERBS = ("exec", "read", "open")
NAME_RE = re.compile(r"[A-Za-z_][\w-]*")
VERIFY_FROM_RE = re.compile(r"\sfrom\s+([A-Za-z_][\w-]*)\s*$")


def bound_names(root, verbs):
    names = set()
    for node in walk(root):
        if node.kind == "action" and node.data in verbs:
            target = as_target(node.text)
            if target:
                names.add(target)
    return names


def input_ask_names(root):
    return {as_target(node.text) for node in walk(root)
            if node.kind == "action" and node.data == "ask" and as_target(node.text)}


def node_class(node, evidence):
    if node.kind == "action":
        if node.data == "exec":
            return "evidence"
        if node.data in ("write", "save"):
            return "effect"
        if node.data == "ask":
            return "user"
        if node.data == "run":
            return "delegated"
        return "self"
    if node.kind == "gate":
        rest = norm(node.text[len(node.data):])
        if node.data == "require" and (rest.startswith("user ") or rest == "confirmation"):
            return "user"
        m = VERIFY_FROM_RE.search(" " + node.text)
        if node.data == "verify" and m and m.group(1) in evidence:
            return "evidence"
        return "self"
    return "self"


def branch_controller(node, evidence, asks):
    words = set(NAME_RE.findall(node.text.split(None, 1)[1] if " " in node.text else ""))
    if words & asks:
        return "user"
    if words & evidence:
        return "evidence"
    return "model"


def classify(root):
    """Gates and branches of one flow with their classes, in line order."""
    evidence = bound_names(root, EVIDENCE_VERBS)
    asks = input_ask_names(root)
    gates, branches, steps = [], [], []
    for node in walk(root):
        if node.kind == "gate" and node.data in ("require", "verify"):
            gates.append((node.line, node.text, node_class(node, evidence)))
        elif node.kind == "branch":
            branches.append((node.line, node.text, branch_controller(node, evidence, asks)))
        if node.kind in ("gate", "action"):
            steps.append((node, node_class(node, evidence)))
    return {"gates": gates, "branches": branches, "steps": steps}
