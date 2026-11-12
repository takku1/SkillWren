"""Ordering invariants (0.6): `order:` rules of the form `A before B`.

A rule holds when, on every path through a flow, a statement matching A has
completed before any statement matching B starts. "Completed" means a gate
passed: a failed `require`/`verify` establishes nothing, because its repair
edge carries the facts from before the gate. A `run` satisfies A when every
returning path of the called flow satisfies A (the callee guarantees it).

Patterns are statement prefixes, compared after lowercasing and collapsing
spaces; `*` matches any text inside a statement. This is a must-analysis
over the control-flow graph, in the spirit of typestate checking and of
Before/After predicates in agent runtime monitors. It reasons about the
written procedure, not about what a model actually does at run time.
"""
import fnmatch

from .flowgraph import is_run, must_facts, returning_exits
from .syntax import Diag, norm


def matches(pattern, text):
    return fnmatch.fnmatchcase(norm(text), norm(pattern) + "*")


def order_facts(root, reach, preds, rules, run_guarantees):
    """in_facts per node: indices of rules whose earlier step has completed.

    run_guarantees(run_node, pattern) -> bool says whether a run's callee
    completes the pattern on every returning path."""
    gen = {}
    for node in reach:
        done = set()
        for k, rule in enumerate(rules):
            if node.kind in ("unknown", "misplaced-invariant"):
                continue
            if matches(rule.first, node.text):
                done.add(k)
            elif is_run(node) and run_guarantees(node, rule.first):
                done.add(k)
        if done:
            gen[node] = done
    universe = set(range(len(rules)))
    in_facts, _ = must_facts(root, reach, preds, gen, {}, set(), universe)
    return in_facts


def guarantees(root, reach, preds, pattern, run_guarantees):
    """True when every returning exit of the flow is preceded by pattern."""
    exits = returning_exits(reach)
    if not exits:
        return False

    class _Rule:
        first = pattern
    in_facts = order_facts(root, reach, preds, [_Rule], run_guarantees)
    return all(0 in in_facts[node] for node in exits)


def check_order(flow_nodes, reach, in_facts, rules, errors):
    """P1 for every reachable later step whose earlier step may not have run.
    Returns the set of rule indices whose later step occurs in this flow."""
    seen = set()
    for node in flow_nodes:
        if node not in reach or node.kind in ("unknown", "misplaced-invariant"):
            continue
        for k, rule in enumerate(rules):
            if not matches(rule.then, node.text):
                continue
            seen.add(k)
            if matches(rule.first, node.text):
                continue  # a statement cannot precede itself
            if k not in in_facts[node]:
                errors.append(Diag(node.line, "P1",
                                   f"{node.text!r} can run before {rule.first!r}"
                                   f" (order rule, line {rule.line})",
                                   f"Make `{rule.first}` (or a run that always performs it)"
                                   " complete on every path to this statement."))
    return seen
