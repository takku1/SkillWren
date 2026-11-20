"""Exclusion order rules (SPEC 23): `never A before B`.

P1 says B needs A first: a must-analysis over every path. An exclusion says
B must not start once A may have run: a may-analysis over some path. The
field case (full-stack, 2026-11-19) was one fragment's `write` making another
fragment's start gate refuse; each fragment checked clean alone.

Scope. A rule declared in file F applies to F's flows and to every flow that
runs a flow of F, directly or transitively, because the conflict usually
spans a composition boundary. A `run` counts as the later step when its
callee may start it, and as the earlier step when its callee may run it.
Callee summaries over-approximate (any reachable matching statement, even
one reached only before an abort), so P3 can report a conflict on a path
that never returns; it never misses one written as `run`. A callee's
internal order is checked by the rules in scope for the callee itself.
"""
from .flowgraph import build_cfg, is_run, predecessors, reachable_nodes, walk
from .ordering import matches
from .syntax import Diag, run_target


def may_facts(reach, preds, gen):
    """Forward may-analysis: a fact holds at a node if it holds on some path."""
    in_facts = {node: set() for node in reach}
    out_facts = {node: set(gen.get(node, ())) for node in reach}
    changed = True
    while changed:
        changed = False
        for node in reach:
            new_in = set().union(*(out_facts[p] for p in preds[node] if p in reach)) \
                if preds[node] else set()
            new_out = new_in | gen.get(node, set())
            if new_in != in_facts[node] or new_out != out_facts[node]:
                in_facts[node], out_facts[node] = new_in, new_out
                changed = True
    return in_facts


def _skip(node):
    return node.kind in ("unknown", "misplaced-invariant")


class Exclusions:
    """Callee summaries for exclusion checks, cached per workspace."""

    def __init__(self, workspace):
        self.workspace = workspace
        self._starts, self._exports, self._loading = {}, {}, set()

    def callee(self, doc, node):
        """(callee_doc, flow) for a resolvable run node, else None."""
        rt = run_target(node.text)
        if not rt:
            return None
        target, rel = rt
        if rel is None:
            return (doc, target) if "." not in target and target in doc.trees else None
        found = self.workspace.resolve_path(doc, rel)
        if found is None:
            return None
        callee = self.workspace.document(found)
        return (callee, target) if callee.readable and target in callee.trees else None

    def _runs(self, doc, flow):
        for node in walk(doc.trees[flow]):
            if is_run(node):
                target = self.callee(doc, node)
                if target:
                    yield node, target

    def may_start(self, doc, flow, pattern):
        """True when some reachable statement of flow, or of a flow it runs,
        matches pattern."""
        key = ("start", doc.path, flow, pattern)
        if key in self._starts:
            return self._starts[key]
        if key in self._loading:
            return False
        self._loading.add(key)
        try:
            root = doc.trees[flow]
            succ, _ = build_cfg(root, None, None)
            reach = reachable_nodes(root, succ)
            result = any(not _skip(n) and matches(pattern, n.text) for n in reach)
            if not result:
                result = any(n in reach and self.may_start(c, f, pattern)
                             for n, (c, f) in self._runs(doc, flow))
        finally:
            self._loading.discard(key)
        self._starts[key] = result
        return result

    def exported(self, doc, flow):
        """Exclusion rules a caller of flow must respect: the callee file's
        own, plus those of everything it runs. Items are (doc, rule)."""
        key = ("export", doc.path, flow)
        if key in self._exports:
            return self._exports[key]
        if key in self._loading:
            return []
        self._loading.add(key)
        try:
            found = [(doc, rule) for rule in doc.contract.exclusions]
            for _, (callee, target) in self._runs(doc, flow):
                found += self.exported(callee, target)
        finally:
            self._loading.discard(key)
        unique = list({(d.path, r.line): (d, r) for d, r in found}.values())
        self._exports[key] = unique
        return unique


def check_exclusions(doc, workspace, errors):
    """P3 for every flow in doc. Returns the set of own-rule indices whose
    later step occurs (directly or through a run) in some flow of doc."""
    summaries = workspace.exclusions
    own = list(doc.contract.exclusions)
    seen = set()
    for root in doc.trees.values():
        succ, _ = build_cfg(root, None, None)
        reach = reachable_nodes(root, succ)
        preds = predecessors(reach, succ)
        runs = {node: summaries.callee(doc, node) for node in reach if is_run(node)}
        rules = [(doc, rule) for rule in own]
        for target in runs.values():
            if target:
                rules += summaries.exported(*target)
        rules = list({(d.path, r.line): (d, r) for d, r in rules}.values())
        for source, rule in rules:
            def hit(node, pattern):
                if _skip(node):
                    return False
                if matches(pattern, node.text):
                    return True
                target = runs.get(node)
                return bool(target) and summaries.may_start(*target, pattern)
            gen = {node: {0} for node in reach if hit(node, rule.first)}
            if not gen:
                continue
            in_facts = may_facts(reach, preds, gen)
            for node in sorted(reach, key=lambda n: n.line):
                if not hit(node, rule.then):
                    continue
                if source is doc:
                    seen.add(own.index(rule))
                if 0 not in in_facts[node]:
                    continue
                where = "" if source is doc else f" in {source.path.name}"
                errors.append(Diag(node.line, "P3",
                                   f"{node.text!r} can start after {rule.first!r} has run"
                                   f" (exclusion rule, line {rule.line}{where})",
                                   "Reorder so the later step runs first, narrow the rule's"
                                   " earlier step, or remove the conflicting effect."))
    for k, rule in enumerate(own):
        for root in doc.trees.values():
            succ, _ = build_cfg(root, None, None)
            if any(not _skip(n) and matches(rule.then, n.text)
                   for n in reachable_nodes(root, succ)):
                seen.add(k)
    return seen
