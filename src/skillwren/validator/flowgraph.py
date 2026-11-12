"""Flow structure: the indentation AST, the control-flow graph, dominators,
and one forward must-dataflow solver shared by binding and ordering checks.

Rules emitted here are purely structural: V1 (unknown statements), O1
(nesting), L1 (labels), L3 (retry ownership), W9 (repair fall-through).
"""
import re

from .syntax import (ACTIONS, ASSIGN_RE, BRANCH, GATES, VAR_ONLY, Diag)


def classify_flow_line(text):
    """Kinds: label/otherwise/else/returnblock/returnto/foreach/branch/gate/
    action/assign/bareword/retry/misplaced-invariant/unknown."""
    if text == "otherwise:":
        return ("otherwise", None)
    if text == "else:":
        return ("else", None)
    if text == "return:":
        return ("returnblock", None)
    if text == "retry":
        return ("retry", None)
    m = re.fullmatch(r"label\s+([^:]+):", text)
    if m:
        return ("label", m.group(1).strip())
    if text.startswith("return to "):
        return ("returnto", text[len("return to "):].strip())
    if text.startswith("for each ") and text.endswith(":"):
        inner = text[len("for each "):-1]
        m2 = re.fullmatch(r"(.+?)\s+as\s+([A-Za-z_][\w-]*)", inner)
        if m2:
            return ("foreach", {"source": m2.group(1).strip(),
                                "var": m2.group(2)})
        return ("unknown", None)
    head = text.split(None, 1)[0]
    if head in BRANCH:
        return ("branch", head) if text.endswith(":") else ("unknown", None)
    if head in GATES:
        return ("gate", head)
    if head in ACTIONS:
        return ("action", head)
    if head in ("always", "never"):
        return ("misplaced-invariant", head)
    if ASSIGN_RE.match(text):
        return ("assign", None)
    if VAR_ONLY.fullmatch(text):
        return ("bareword", text)
    return ("unknown", None)


class Node:
    """One flow statement in the indentation AST."""
    __slots__ = ("line", "indent", "text", "kind", "data", "children",
                 "parent")

    def __init__(self, line, indent, text, kind, data):
        self.line = line
        self.indent = indent
        self.text = text
        self.kind = kind
        self.data = data
        self.children = []
        self.parent = None


def walk(root):
    """All AST nodes in pre-order, excluding the root."""
    out = []
    stack = list(reversed(root.children))
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(reversed(node.children))
    return out


def is_fallible(node):
    if node.kind == "gate" and node.data in ("require", "verify"):
        return True
    return node.kind == "action" and node.data in ("read", "open")


def is_run(node):
    return node.kind == "action" and node.data == "run"


def is_terminal(node):
    if node.kind == "returnblock":
        return True
    return node.kind == "action" and node.data in ("return", "abort")


def check_nesting(parent, node, diags):
    """O1/V1 block-structure rules. Labels never parent (transparent)."""
    kind = node.kind
    if kind == "otherwise":
        if not is_fallible(parent):
            diags.append(Diag(
                node.line, "O1", "otherwise: without a fallible gate",
                "Nest it directly under require, verify, read, or open."))
        return
    if kind in ("assign", "bareword"):
        if parent.kind != "returnblock" and not is_run(parent):
            if kind == "assign":
                diags.append(Diag(node.line, "V1",
                                  f"stray assignment {node.text!r}",
                                  "Assignments live in run args or return: blocks."))
            else:
                diags.append(Diag(node.line, "V1",
                                  f"stray name {node.text!r}",
                                  "Bare names live in return: blocks only."))
        return
    if kind == "else":
        siblings = parent.children
        idx = siblings.index(node)
        if idx == 0 or siblings[idx - 1].kind != "branch":
            diags.append(Diag(node.line, "O1", "else: without a preceding if, unless, or when",
                              "Place else: right after a branch block, at the same indentation."))
            return
    if parent.kind in ("root", "branch", "foreach", "otherwise", "else"):
        return
    if parent.kind == "returnblock":
        diags.append(Diag(node.line, "O1",
                          f"{node.text!r} is not a return value",
                          "Use one `name` or `name = binding` line per value."))
        return
    if is_run(parent):
        diags.append(Diag(node.line, "O1",
                          f"{node.text!r} is not a run argument",
                          "Use `name = value` lines under run."))
        return
    if is_fallible(parent):
        diags.append(Diag(node.line, "O1",
                          f"{node.text!r} cannot nest under a gate",
                          "Only otherwise: may nest under require, verify,"
                          " read, or open."))
        return
    diags.append(Diag(node.line, "O1", f"{node.text!r} cannot nest here",
                      "Dedent it or move it into a branch or repair block."))


def build_tree(stmts, diags):
    """Nest flat (lineno, indent, text) statements into an indentation AST.

    Labels are transparent markers: indented lines never attach under them.
    Emits V1 (unknown statements, stray names) and O1 (bad nesting).
    """
    root = Node(0, -1, "", "root", None)
    stack = [root]
    for ln, ind, text in stmts:
        kind, data = classify_flow_line(text)
        node = Node(ln, ind, text, kind, data)
        while len(stack) > 1 and (ind <= stack[-1].indent
                                  or stack[-1].kind == "label"):
            stack.pop()
        parent = stack[-1]
        node.parent = parent
        parent.children.append(node)
        stack.append(node)
        if kind == "unknown":
            diags.append(Diag(ln, "V1", f"unknown statement {text!r}",
                              "Use only the v0.6 verb set."))
        elif kind == "misplaced-invariant":
            diags.append(Diag(ln, "V1", f"{data} outside the contract block",
                              "Move invariants to the contract block."))
        check_nesting(parent, node, diags)
    return root


END = object()  # sentinel: virtual flow exit


def following_else(node):
    """The else: block attached to a branch node, if any."""
    if node.kind != "branch":
        return None
    sibs = node.parent.children
    idx = sibs.index(node)
    if idx + 1 < len(sibs) and sibs[idx + 1].kind == "else":
        return sibs[idx + 1]
    return None


def next_after(node):
    parent = node.parent
    idx = parent.children.index(node)
    if idx + 1 < len(parent.children):
        nxt = parent.children[idx + 1]
        if nxt.kind == "else" and node.kind == "branch":
            return next_after(nxt)  # leaving the if-arm skips its else-arm
        return nxt
    if parent.kind == "root":
        return END
    return next_after(parent)


def enclosing_foreach_source(node, name):
    """True when name is the iterated collection of an enclosing loop."""
    parent = node.parent
    while parent is not None and parent.kind != "root":
        if parent.kind == "foreach" and parent.data["source"] == name:
            return True
        parent = parent.parent
    return False


def retry_owner(node):
    """Nearest enclosing repair gate, or None. Stops at the nearest
    otherwise: block even when that block is itself misplaced."""
    parent = node.parent
    while parent is not None and parent.kind != "root":
        if parent.kind == "otherwise":
            gate = parent.parent
            return gate if is_fallible(gate) else None
        parent = parent.parent
    return None


def ends_repair(node):
    return node.kind in ("retry", "returnto", "returnblock") \
        or is_terminal(node)


def emit(diags, diag):
    if diags is not None:
        diags.append(diag)


def successors(node, labels, diags):
    kind = node.kind
    if node.parent is not None and node.parent.kind == "returnblock":
        sibs = node.parent.children
        idx = sibs.index(node)
        if idx + 1 < len(sibs):
            return [sibs[idx + 1]]
        return []  # the block is terminal past its last value
    if kind == "returnblock":
        return [node.children[0]] if node.children else []
    if is_terminal(node):
        return []
    if kind == "otherwise":
        if node.children:
            return [node.children[0]]
        return [next_after(node)]
    if is_run(node):
        nxt = next_after(node)
        return [node.children[0]] if node.children else [nxt]
    if is_fallible(node):
        nxt = next_after(node)
        repairs = [c for c in node.children if c.kind == "otherwise"]
        if not repairs:
            return [nxt]
        return [nxt, repairs[0]]
    if kind == "else":
        return [node.children[0]] if node.children else [next_after(node)]
    if kind in ("branch", "foreach"):
        otherwise_arm = following_else(node)
        nxt = otherwise_arm if otherwise_arm is not None else next_after(node)
        if node.children:
            return [node.children[0], nxt]
        return [nxt]
    if kind == "retry":
        owner = retry_owner(node)
        if owner is None:
            emit(diags, Diag(node.line, "L3", "retry outside a repair block",
                             "Use retry only inside otherwise: under require,"
                             " verify, read, or open."))
            return [next_after(node)]
        return [owner]
    if kind == "returnto":
        if node.data in labels:
            return [labels[node.data]]
        emit(diags, Diag(node.line, "L1",
                         f"return to unknown label {node.data!r}",
                         f"Declare it with `label {node.data}:`."))
        return [next_after(node)]
    return [next_after(node)]


def build_cfg(root, errors, warnings):
    """Returns (succ, labels). Emits L1 (labels), L3 (retry), W9
    (otherwise fall-through) unless the diag lists are None (silent
    pre-pass). Extra otherwise: blocks after the first are left
    unreachable (W10) rather than given semantics."""
    nodes = walk(root)
    labels = {}
    for node in nodes:
        if node.kind == "label":
            if node.data in labels:
                emit(errors, Diag(node.line, "L1",
                                  f"duplicate label {node.data!r}",
                                  "Keep label names unique per flow."))
            else:
                labels[node.data] = node
    succ = {node: successors(node, labels, errors) for node in nodes}
    for node in nodes:
        if node.kind == "otherwise" and (
                not node.children or not ends_repair(node.children[-1])):
            emit(warnings, Diag(
                node.line, "W9", "otherwise: block falls through",
                "End it with retry, return to, abort, or return."))
        if node.kind == "foreach" and node.children:
            last = node.children[-1]
            if succ[last] and not is_terminal(last) \
                    and last.kind not in ("returnto", "retry"):
                succ[last].append(node.children[0])
    return succ, labels


def reachable_nodes(root, succ):
    seen = set()
    entry = root.children[0] if root.children else END
    stack = [entry]
    while stack:
        node = stack.pop()
        if node is END or node in seen:
            continue
        seen.add(node)
        stack.extend(succ.get(node, ()))
    return seen


def predecessors(reach, succ):
    preds = {node: set() for node in reach}
    for node in reach:
        for nxt in succ.get(node, ()):
            if nxt is not END and nxt in preds:
                preds[nxt].add(node)
    return preds


def dominators(root, succ, reach, preds):
    entry = root.children[0] if root.children else None
    dom = {node: set(reach) for node in reach}
    if entry is not None:
        dom[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for node in reach:
            if node is entry:
                continue
            ins = [dom[p] for p in preds[node]]
            new = {node} | (set.intersection(*ins) if ins else set())
            if new != dom[node]:
                dom[node] = new
                changed = True
    return dom


def is_fail_edge(pred, node):
    """The edge from a fallible gate into its own otherwise: repair."""
    return node.kind == "otherwise" and node.parent is pred and is_fallible(pred)


def must_facts(root, reach, preds, gen, kill, entry_facts, universe):
    """Forward must-analysis to a fixpoint. Returns (in_facts, out_facts).

    A fact holds at a node only if it holds on every path from the entry.
    A failed gate establishes nothing: the edge into its otherwise: repair
    carries the facts from before the gate, not after it.
    """
    entry = root.children[0] if root.children else None
    in_facts = {node: set(universe) for node in reach}
    out_facts = {node: set(universe) for node in reach}
    for _ in range(1000):
        changed = False
        for node in reach:
            ins = []
            for pred in preds[node]:
                if is_fail_edge(pred, node):
                    ins.append(in_facts[pred])  # fail edge: pre-gate facts
                else:
                    ins.append(out_facts[pred])
            if node is entry:
                ins.append(set(entry_facts))
            new_in = set.intersection(*ins) if ins else set(entry_facts)
            new_out = (new_in | gen.get(node, set())) - kill.get(node, set())
            if new_in != in_facts[node] or new_out != out_facts[node]:
                in_facts[node], out_facts[node] = new_in, new_out
                changed = True
        if not changed:
            break
    return in_facts, out_facts


def rebound_before(node, name, reach, preds, *gen_maps):
    """True when some path into node rebinds name (searching backwards)."""
    seen, stack = set(), [node]
    while stack:
        cur = stack.pop()
        for pred in preds.get(cur, ()):
            if pred in seen or pred not in reach:
                continue
            seen.add(pred)
            if any(name in gens.get(pred, ()) for gens in gen_maps):
                return True
            stack.append(pred)
    return False


def returning_exits(reach):
    """Reachable nodes where the flow hands control back to its caller
    (return or a return: block; abort ends the run instead)."""
    return [node for node in reach
            if node.kind == "returnblock"
            or (node.kind == "action" and node.data == "return")]
