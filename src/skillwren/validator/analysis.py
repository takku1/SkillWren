"""Per-flow semantic analysis over the AST and CFG.

`FlowAnalysis` scans statements once (vocabulary, effects, bindings), then
runs whole-flow checks in a fixed order: definite binding (U1), deferred
sources (E1), apply purity (E4), loop and argument types (T1, T2),
required-input gates (R4), termination (R2), authority structure (A2),
dismissal safety (M1), and ordering invariants (P1).

In fragment mode (0.6) there is no header: resource and effect checks are
off, any returned name is allowed, and inputs are the contract's `inputs:`
list or, without one, inferred (see `infer_inputs`).
"""
import re

from .flowgraph import (END, build_cfg, dominators, enclosing_foreach_source,
                        is_fallible, is_run, is_terminal, must_facts,
                        predecessors, reachable_nodes, rebound_before, walk)
from .ordering import check_order, order_facts
from .syntax import (ASSIGN_RE, INTERP_RE, VAR_ONLY, WITH_RE, Diag, as_target,
                     content_words, from_source, match_resource, norm,
                     run_target, strip_as_clause, valid_type)

PRESENCE_RE = re.compile(
    r"(?:if|unless|when)\s+([A-Za-z_][\w-]*)\s+(?:is|are)\s+"
    r"(?:known|given|supplied|present|available|provided)\b")
GATE_PRESENCE_RE = re.compile(
    r"(?:require|verify)\s+([A-Za-z_][\w-]*)\s+"
    r"(?:exists|is\s+known|are\s+known|is\s+given|is\s+present)\s*$")


def track_literal(info, key, resource, target):
    if "{" not in target and "}" not in target and "*" not in target:
        info[key].append((resource, target))


def collect_flow_facts(root, produces):
    """Pre-pass: returned names + same-file call edges. No diags.

    produces=None (fragments) accepts every returned name."""
    def declared(name):
        return produces is None or name in produces

    returned, calls = set(), []
    for node in walk(root):
        if node.kind == "action" and node.data == "return":
            m = re.fullmatch(r"return\s+(\S+)\s+as\s+([A-Za-z_][\w-]*)\s*",
                             node.text)
            if m and declared(m.group(2)):
                returned.add(m.group(2))
        elif node.kind == "action" and node.data == "run":
            rt = run_target(node.text)
            if rt and rt[1] is None and "." not in rt[0]:
                calls.append((node.line, rt[0]))
        elif node.kind == "assign" and node.parent.kind == "returnblock":
            m = ASSIGN_RE.match(node.text)
            if m and declared(m.group(1)):
                returned.add(m.group(1))
        elif node.kind == "bareword" and node.parent.kind == "returnblock":
            if declared(node.text):
                returned.add(node.text)
    return returned, calls


def direct_mutation(root):
    """True when a reachable statement writes, saves, or executes."""
    succ, _ = build_cfg(root, None, None)
    reach = reachable_nodes(root, succ)
    return any(node in reach and node.kind == "action"
               and node.data in ("write", "save", "exec")
               for node in walk(root))


def infer_inputs(uses, gen, nodes):
    """Fragment inputs without an `inputs:` list: names that are used but
    never bound in the flow, plus names whose presence the flow tests.
    `require request exists` declares a required input; `unless design is
    known:` declares an optional one. A name bound only on some paths and
    never presence-tested stays subject to U1."""
    bound = set().union(*gen.values()) if gen else set()
    used = {name for pairs in uses.values() for name, _ in pairs}
    tested = set()
    for node in nodes:
        if node.kind == "branch":
            m = PRESENCE_RE.match(node.text)
        elif node.kind == "gate" and node.data in ("require", "verify"):
            m = GATE_PRESENCE_RE.match(node.text)
        else:
            m = None
        if m:
            tested.add(m.group(1))
    return (used - bound) | tested


class FlowAnalysis:
    """One flow's checks. ctx keys: header, resources, nevers, flows,
    callee_out, flow_mutates, fragment, inputs, external, order,
    run_guarantees."""

    def __init__(self, flow, root, header_line, ctx):
        self.flow, self.root, self.header_line = flow, root, header_line
        self.errors, self.warnings = [], []
        self.info = {"edges": [], "returned": set(), "asks": [], "req_users": [],
                     "reads": set(), "binds": {}, "texts": [], "has_generate": False,
                     "covered_reads": set(), "covered_writes": set(),
                     "literal_reads": [], "literal_writes": [],
                     "writes": [], "runs": [], "inputs": []}
        self.header = ctx.get("header") or {}
        self.resources = ctx.get("resources", {})
        self.nevers = ctx.get("nevers", [])
        self.fragment = bool(ctx.get("fragment"))
        self.accepts = set((self.header.get("accepts") or {}).keys())
        self.produces = None if self.fragment else set((self.header.get("produces") or {}).keys())
        self.flows = set(ctx.get("flows", []))
        self.callee_out = ctx.get("callee_out", {})
        self.flow_mutates = ctx.get("flow_mutates", {})
        self.declared_inputs = ctx.get("inputs")
        self.external = ctx.get("external", {})
        self.order = ctx.get("order", [])
        self.run_guarantees = ctx.get("run_guarantees") or (lambda node, pattern: False)

        self.nodes = walk(root)
        self.succ, _ = build_cfg(root, self.errors, self.warnings)
        self.reach = reachable_nodes(root, self.succ)
        for node in self.nodes:
            if node not in self.reach:
                self.warnings.append(Diag(node.line, "W10", "unreachable statement",
                                          "Remove it or fix the control flow."))
        self.preds = predecessors(self.reach, self.succ)
        self.dom = dominators(root, self.succ, self.reach, self.preds)

        self.gen = {node: set() for node in self.nodes}
        self.gen_as = {node: set() for node in self.nodes}
        self.kill = {node: set() for node in self.nodes}
        self.uses = {node: [] for node in self.nodes}
        self.ask_nodes, self.decision_asks = [], []
        self.confirm_user, self.confirm_bare = [], []
        self.apply_nodes, self.run_calls, self.direct_mutations = [], [], []
        self.external_calls = []  # (node, mutates)
        self.pending_from, self.foreach_nodes, self.pending_run_args = [], [], []

    # ------------------------------------------------------------ helpers
    def error(self, line, rule, msg, fix):
        self.errors.append(Diag(line, rule, msg, fix))

    def use(self, node, name, what):
        if name and VAR_ONLY.fullmatch(name):
            self.uses[node].append((name, what))

    def declared_output(self, name):
        return self.produces is None or name in self.produces

    def resolve(self, target):
        return match_resource(target, self.resources)

    # --------------------------------------------------------------- scan
    def scan(self):
        for node in self.nodes:
            self.info["texts"].append(node.text)
            if node.kind in ("unknown", "misplaced-invariant"):
                continue  # V1 already emitted at build
            for var in INTERP_RE.findall(node.text):
                self.use(node, var.strip(), "interpolation")
            handler = getattr(self, "_scan_" + node.kind, None)
            if handler is not None:
                handler(node)

    def _scan_foreach(self, node):
        data = node.data
        self.gen[node].add(data["var"])
        self.gen_as[node].add(data["var"])
        self.info["binds"].setdefault(data["var"], node.line)
        if VAR_ONLY.fullmatch(data["source"]):
            self.use(node, data["source"], "for-each source")
            self.foreach_nodes.append((node, data["source"]))

    def _scan_gate(self, node):
        text, data = node.text, node.data
        rest = text[len(data):].strip()
        if data == "verify":
            m = re.search(r"\sfrom\s+([A-Za-z_][\w-]*)\s*$", rest)
            if m:
                self.use(node, m.group(1), "verify evidence")
        if data == "require" and rest.startswith("user "):
            self.info["req_users"].append(text)
            self.confirm_user.append(node)
        elif data == "require" and norm(rest) == "confirmation":
            self.confirm_bare.append(node)
        if data == "allow":
            if " when " not in text or not text.endswith(":"):
                self.error(node.line, "V1", "malformed allow",
                           "Use `allow <action> when <condition>:`"
                           " quoting one never invariant.")
            elif not any(len(content_words(text) & content_words(never)) >= 2
                         for never in self.nevers):
                self.error(node.line, "A1", "allow matches no never invariant",
                           "Quote the invariant it narrows.")

    def _scan_assign(self, node):
        text = node.text
        if node.parent.kind == "returnblock":
            m = ASSIGN_RE.match(text)
            name, val = m.group(1), m.group(2).strip()
            if not self.declared_output(name):
                self.error(node.line, "R2",
                           f"return names undeclared produces entry {name!r}",
                           "Return a skill produces entry.")
            else:
                self.info["returned"].add(name)
            if VAR_ONLY.fullmatch(val):
                self.use(node, val, "return value")
        elif is_run(node.parent):
            m = ASSIGN_RE.match(text)
            val = m.group(2).strip()
            if VAR_ONLY.fullmatch(val):
                self.use(node, val, "run argument value")
                self.pending_run_args.append((node, node.parent, m.group(1), val))
        # elsewhere: V1 stray already emitted at build

    def _scan_bareword(self, node):
        text = node.text
        if node.parent.kind == "returnblock":
            if not self.declared_output(text):
                self.error(node.line, "R2",
                           f"return names undeclared produces entry {text!r}",
                           "Return a skill produces entry.")
            else:
                self.info["returned"].add(text)
            self.use(node, text, "return value")

    def _scan_action(self, node):
        text, verb = node.text, node.data
        rest = text[len(verb):].strip()
        if verb == "generate":
            self.info["has_generate"] = True
            self.info.setdefault("gen_line", node.line)
        tgt = as_target(text)
        if tgt and VAR_ONLY.fullmatch(tgt) and verb not in ("save", "write", "return"):
            self.gen[node].add(tgt)
            self.gen_as[node].add(tgt)
            self.info["binds"].setdefault(tgt, node.line)
        if tgt and VAR_ONLY.fullmatch(tgt):
            if verb in ("save", "write"):
                self.gen_as[node].add(tgt)
            self._loop_rebinding(node, tgt)
        getattr(self, "_verb_" + verb)(node, rest, tgt)
        if verb != "read":
            src = from_source(text)
            # An exec source is a place (a declared resource, or in a
            # fragment an undeclared one), not a binding to read.
            if src and VAR_ONLY.fullmatch(src) \
                    and not (verb == "exec" and (self.resolve(src) or self.fragment)):
                self.use(node, src, "from source")

    def _loop_rebinding(self, node, tgt):
        parent = node.parent
        while parent is not None and parent.kind != "root":
            if parent.kind == "foreach":
                if parent.data["var"] == tgt:
                    self.error(node.line, "L1", f"mutation of for-each variable {tgt!r}",
                               "Bind a new name instead.")
                    return
                if parent.data["source"] == tgt:
                    self.error(node.line, "L1", f"mutation of for-each collection {tgt!r}",
                               "Do not write to the iterated collection inside the loop.")
                    return
            parent = parent.parent

    def _target_error(self, node, msg, fix):
        if not self.fragment:  # fragments declare no resources
            self.error(node.line, "E1", msg, fix)

    def _verb_open(self, node, rest, tgt):
        target = strip_as_clause(rest)
        if not target:
            self.error(node.line, "E1", "open names no target",
                       "Name a resource, path, or accepts entry.")
            return
        name = self.resolve(target)
        if not name and target not in self.accepts:
            self._target_error(node, f"open target {target!r} matches no resource, path, or accepts entry",
                               "Declare the resource or fix the name.")
        elif name:
            self.info["covered_reads"].add(name)
            track_literal(self.info, "literal_reads", name, target)

    def _verb_read(self, node, rest, tgt):
        src = from_source(node.text)
        if src is not None:
            name = self.resolve(src)
            if name:
                self.info["covered_reads"].add(name)
                track_literal(self.info, "literal_reads", name, src)
            elif VAR_ONLY.fullmatch(src):
                self.pending_from.append((node, src))
            else:
                self._target_error(node, f"read source {src!r} matches no resource, path, or accepts entry",
                                   "Declare the resource or fix the name.")
            return
        target = strip_as_clause(rest)
        if not target:
            self.error(node.line, "E1", "read names no target",
                       "Name a path or use `read X from Y`.")
            return
        name = self.resolve(target)
        if not name and target not in self.accepts:
            self._target_error(node, f"read target {target!r} matches no resource, path, or accepts entry",
                               "Declare the resource or fix the name.")
        elif name:
            self.info["covered_reads"].add(name)
            track_literal(self.info, "literal_reads", name, target)

    def _verb_exec(self, node, rest, tgt):
        self.direct_mutations.append(node)  # a command may change anything it can reach
        if not (tgt and VAR_ONLY.fullmatch(tgt)):
            self.error(node.line, "V1", "exec without `as` discards its result",
                       "Bind the outcome with `as <name>` so a gate can cite it.")
        src = from_source(node.text)
        name = self.resolve(src) if src else None
        if not src:
            self.error(node.line, "E1", "exec names no resource",
                       "Use `exec <command> from <resource> as <name>`.")
        elif not name and src not in self.accepts:
            self._target_error(node, f"exec source {src!r} matches no resource, path, or accepts entry",
                               "Declare the resource the command runs in or from.")
        elif name:
            self.info.setdefault("covered_execs", set()).add(name)

    def _verb_write(self, node, rest, tgt):
        self._mutation(node, "write", rest, tgt)

    def _verb_save(self, node, rest, tgt):
        self._mutation(node, "save", rest, tgt)

    def _mutation(self, node, verb, rest, tgt):
        self.direct_mutations.append(node)
        if verb == "write":
            m = WITH_RE.search(node.text)
            target = m.group(1).strip() if m else ""
            val = rest.split(" with ", 1)[0].strip()
        else:
            target = tgt or ""
            val = rest.rsplit(" as ", 1)[0].strip() if " as " in rest else ""
        self.info["writes"].append(target)
        if VAR_ONLY.fullmatch(val):
            self.use(node, val, f"{verb} value")
        name = self.resolve(target) if target else None
        if verb == "write" and VAR_ONLY.fullmatch(target) \
                and enclosing_foreach_source(node, target):
            self.error(node.line, "L1", f"mutation of for-each collection {target!r}",
                       "Do not write to the iterated collection inside the loop.")
        if not target:
            self.error(node.line, "E1", f"{verb} target {target!r} matches no resource, path, or accepts entry",
                       "Declare the resource or fix the path.")
        elif not name and target not in self.accepts:
            self._target_error(node, f"{verb} target {target!r} matches no resource, path, or accepts entry",
                               "Declare the resource or fix the path.")
        elif name:
            self.info["covered_writes"].add(name)
            track_literal(self.info, "literal_writes", name, target)
            if str(self.resources[name].get("immutable", "")).lower() == "true":
                self.error(node.line, "E3", f"{verb} to immutable resource {name!r}",
                           "Write elsewhere or drop immutable:.")

    def _verb_show(self, node, rest, tgt):
        if VAR_ONLY.fullmatch(rest):
            self.use(node, rest, "show value")

    def _verb_discard(self, node, rest, tgt):
        if VAR_ONLY.fullmatch(rest):
            self.use(node, rest, "discard value")
            self.kill[node].add(rest)

    def _verb_ask(self, node, rest, tgt):
        self.ask_nodes.append(node)
        self.info.setdefault("all_asks", []).append(node.text)
        if not (tgt and VAR_ONLY.fullmatch(tgt)):
            self.decision_asks.append(node)
            self.info["asks"].append((node.line, node.text))

    def _verb_generate(self, node, rest, tgt):
        pass  # binding and appendix bookkeeping happen in _scan_action

    def _verb_apply(self, node, rest, tgt):
        m = WITH_RE.search(node.text)
        target = m.group(1).strip() if m else ""
        if not (tgt and VAR_ONLY.fullmatch(tgt)):
            self.error(node.line, "V1", "apply without `as` discards its result",
                       "Bind the outcome with `as <name>`.")
        if VAR_ONLY.fullmatch(target) and not self.resolve(target):
            self.use(node, target, "apply target")
        self.apply_nodes.append((node, target))

    def _verb_run(self, node, rest, tgt):
        rt = run_target(node.text)
        if not rt:
            self.error(node.line, "V1", f"malformed run {node.text!r}",
                       "Use `run <flow> with:` (or `run <flow> from <file> with:`)"
                       " plus indented args.")
            return
        target, path = rt
        self.info["runs"].append(f"{target} from {path}" if path else target)
        if path is not None:
            ext = self.external.get((target, path))
            if ext is None or ext.get("error"):
                reason = ext["error"] if ext else f"cannot resolve {path!r}"
                self.error(node.line, "R3", f"run target {target!r}: {reason}",
                           "Point `from` at a file (relative to this file or its skill root)"
                           " whose logic block declares the flow.")
                return
            self.gen[node].update(ext["returned"])
            self.external_calls.append((node, ext["mutates"]))
            if not self.fragment:
                self.warnings.append(Diag(node.line, "W8",
                                          f"cross-file run {target!r} from {path!r}: effects are"
                                          " not reconciled with this header",
                                          "Declare the callee's effects here too, or run it as a fragment."))
            return
        if "." in target:
            self.warnings.append(Diag(node.line, "W8",
                                      f"cross-skill run {target!r} is an unverified effect boundary",
                                      "Resolve it with a workspace validator; keep accepts aligned."))
        elif target not in self.flows:
            self.error(node.line, "R3", f"run target {target!r} is no flow in this file",
                       "Run a declared flow.")
        else:
            self.info["edges"].append((node.line, target))
            self.gen[node].update(self.callee_out.get(target, set()))
            self.run_calls.append((node, target))

    def _verb_return(self, node, rest, tgt):
        m = re.fullmatch(r"return\s+(\S+)\s+as\s+([A-Za-z_][\w-]*)\s*", node.text)
        if not m:
            self.error(node.line, "V1", f"malformed return {node.text!r}",
                       "Use `return <binding> as <name>` or a `return:` block.")
            return
        val, name = m.group(1), m.group(2)
        if VAR_ONLY.fullmatch(val):
            self.use(node, val, "return value")
        if not self.declared_output(name):
            self.error(node.line, "R2", f"return names undeclared produces entry {name!r}",
                       "Return a skill produces entry.")
        else:
            self.info["returned"].add(name)

    def _verb_abort(self, node, rest, tgt):
        pass

    # -------------------------------------------------------- whole-flow
    def bindings(self):
        if self.fragment:
            if self.declared_inputs is not None:
                self.accepts = set(self.declared_inputs)
            else:
                self.accepts = infer_inputs(self.uses, self.gen, self.nodes)
            self.info["inputs"] = sorted(self.accepts)
        self.ever = set(self.accepts)
        for node in self.nodes:
            self.ever |= self.gen[node]
        self.in_facts, _ = must_facts(self.root, self.reach, self.preds, self.gen,
                                      self.kill, self.accepts, self.ever)

    def check_unbound(self):
        for node in self.reach:
            for name, what in self.uses[node]:
                self.info["reads"].add(name)
                if name not in self.in_facts[node]:
                    if name in self.ever:
                        msg = f"{what} {name!r} may be unbound on some path"
                        fix = "Bind it on every path to this use."
                    else:
                        msg = f"{what} {name!r} is not bound"
                        fix = ("Bind it with `as` or list it under the contract's inputs:."
                               if self.fragment else
                               "Bind it with `as` or declare it in accepts:.")
                    self.error(node.line, "U1", msg, fix)

    def check_deferred_sources(self):
        for node, src in self.pending_from:
            if node in self.reach:
                self.info["reads"].add(src)
                resolve = self.in_facts[node]
            else:
                resolve = self.ever
            if src not in resolve and not self.fragment:
                self.error(node.line, "E1",
                           f"read source {src!r} matches no resource, path, or accepts entry",
                           "Declare the resource or fix the name.")

    def check_apply_purity(self):
        for node, target in self.apply_nodes:
            if not target:
                continue
            resolve = self.in_facts[node] if node in self.reach else self.ever
            if self.resolve(target) and target not in resolve:
                self.error(node.line, "E4",
                           f"apply target {target!r} is a resource, but apply is pure",
                           "Read it into a binding first, then apply to the binding.")

    def accepts_map(self):
        accepts = self.header.get("accepts")
        return accepts if isinstance(accepts, dict) else {}

    def check_loop_types(self):
        accepts_map = self.accepts_map()
        for node, src in self.foreach_nodes:
            if node not in self.reach or src not in self.in_facts[node]:
                continue  # unreachable, or U1 owns unbound sources
            entry = accepts_map.get(src)
            if not isinstance(entry, dict) or "type" not in entry:
                continue  # untyped binding: needs dataflow inference (future work)
            typ = str(entry["type"])
            if not valid_type(typ) or typ == "Any" or typ.startswith("List<"):
                continue  # F1 owns malformed; Any admits List
            if not rebound_before(node, src, self.reach, self.preds, self.gen_as):
                self.error(node.line, "T1",
                           f"for each source {src!r} has type {typ}, not a List type",
                           "Iterate a List-typed binding.")

    def check_run_arg_types(self):
        accepts_map = self.accepts_map()
        for node, run_node, name, val in self.pending_run_args:
            rt = run_target(run_node.text)
            if not rt:
                continue  # V1 owns malformed runs
            target, path = rt
            if path is not None or "." in target or target not in self.flows:
                continue  # W8 owns foreign runs; R3 owns unknown targets
            if node not in self.reach or val not in self.in_facts[node]:
                continue  # unreachable, or U1 owns unbound values
            want, got = accepts_map.get(name), accepts_map.get(val)
            if not isinstance(want, dict) or not isinstance(got, dict):
                continue  # locals and untyped bindings have no declared type
            if "type" not in want or "type" not in got:
                continue
            want_t, got_t = str(want["type"]), str(got["type"])
            if not valid_type(want_t) or not valid_type(got_t):
                continue  # F1 owns malformed types
            if want_t == "Any" or got_t == "Any":
                continue  # Any admits every type
            if re.sub(r"\s+", "", want_t) == re.sub(r"\s+", "", got_t):
                continue
            # gen_as covers as/generate rebinding; gen additionally covers
            # run outputs, which rebind to unknown types too.
            if not rebound_before(node, val, self.reach, self.preds, self.gen_as, self.gen):
                self.error(node.line, "T2",
                           f"run argument {name!r} wants {want_t} but {val!r} has type {got_t}",
                           "Pass a binding of the declared accepts type.")

    def leading_requires(self):
        leading = []
        for child in self.root.children:
            if child.kind == "label":
                continue
            if child.kind == "gate" and child.data == "require":
                leading.append(child.text[len("require"):].strip())
            else:
                break
        self.info["leading"] = leading
        return leading

    def check_required_inputs(self, leading):
        used = set()
        for node in self.reach:
            used.update(name for name, _ in self.uses[node])
        used.update(src for node, src in self.pending_from if node in self.reach)
        required = {name for name, entry in (self.header.get("accepts") or {}).items()
                    if isinstance(entry, dict) and entry.get("required") == "true"}
        gates = [norm(c) for c in leading]
        for name in sorted(required):
            if name in used and norm(f"{name} exists") not in gates:
                self.error(self.header_line, "R4",
                           f"required input {name!r} is used but never gated",
                           f"Add a leading `require {name} exists`.")

    def check_termination(self):
        def ends_flow(node):
            return node.kind == "returnblock" \
                or (node.parent is not None and node.parent.kind == "returnblock") \
                or is_terminal(node)

        for node in self.reach:
            out = self.succ.get(node, [])
            if (not out or END in out) and not ends_flow(node):
                self.error(node.line, "R2", "flow falls off the end without return or abort",
                           "End every path with a return or abort.")
        if not any(node.kind == "returnblock" or is_terminal(node) for node in self.reach):
            self.error(self.header_line, "R2", "flow has no reachable return or abort",
                       "End the flow with a return or abort.")

    def check_authority(self):
        reach, dom = self.reach, self.dom
        for node in self.confirm_user:
            if node in reach and not any(d in dom[node] for d in self.decision_asks if d in reach):
                self.error(node.line, "A2", "user decision without a preceding ask",
                           "Ask the user before requiring their decision.")
        for node in self.decision_asks:
            if node in reach and not any(node in dom[c] for c in self.confirm_user + self.confirm_bare
                                         if c in reach):
                self.error(node.line, "A2", "decision ask without a following confirmation",
                           "Add `require confirmation` or `require user ...` after it.")
        for node in self.confirm_bare:
            if node in reach and not any(a in dom[node] for a in self.ask_nodes if a in reach):
                self.error(node.line, "A2", "confirmation without a preceding ask",
                           "Ask before requiring confirmation.")

    def check_dismissal(self):
        reach = self.reach
        mut_nodes = {node for node in self.direct_mutations if node in reach}
        mut_nodes |= {node for node, target in self.run_calls
                      if node in reach and self.flow_mutates.get(target, False)}
        mut_nodes |= {node for node, mutates in self.external_calls if node in reach and mutates}
        if not mut_nodes:
            return
        for ask in self.ask_nodes:
            if ask not in reach:
                continue
            seen, stack, hit = set(), [ask], None
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                if cur in mut_nodes and (hit is None or cur.line < hit.line):
                    hit = cur
                stack.extend(p for p in self.preds.get(cur, ()) if p in reach)
            if hit is not None:
                self.error(ask.line, "M1",
                           f"ask after a mutation (line {hit.line}) breaks dismissal safety",
                           "Move mutations after the confirmation, or remove the ask.")

    def check_ordering(self):
        if not self.order:
            self.info["order_seen"] = set()
            return
        in_facts = order_facts(self.root, self.reach, self.preds, self.order,
                               self.run_guarantees)
        self.info["order_seen"] = check_order(self.nodes, self.reach, in_facts,
                                              self.order, self.errors)

    def run(self):
        self.scan()
        self.bindings()
        self.check_unbound()
        self.check_deferred_sources()
        self.check_apply_purity()
        self.check_loop_types()
        self.check_run_arg_types()
        leading = self.leading_requires()
        self.check_required_inputs(leading)
        self.check_termination()
        self.check_authority()
        self.check_dismissal()
        self.check_ordering()
        return self.errors, self.warnings, self.info


def analyze_flow(flow, root, header_line, ctx):
    """Returns (errors, warnings, info) for one flow."""
    return FlowAnalysis(flow, root, header_line, ctx).run()
