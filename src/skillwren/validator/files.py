"""File-level validation: skill files, flow fragments, and the workspace
that resolves `run <flow> from <file> with:` across files.

Skill layout (default) checks a complete SkillWren skill: header schema,
contract, flows, effects, authority, and budgets. Fragment layout (0.6)
checks the logic blocks embedded in an ordinary Markdown file, such as the
on-demand flow files of a skill whose `SKILL.md` keeps only `name` and
`description`. Both share the AST, CFG, dataflow, and ordering analyses.
"""
import math
import re
from pathlib import Path

from .analysis import analyze_flow, collect_flow_facts, direct_mutation
from .document import parse_fences, read_contract
from .flowgraph import build_cfg, build_tree, predecessors, reachable_nodes, walk
from .evidence import classify
from .ordering import guarantees, matches
from .schema import check_schema
from .syntax import (APPENDIX_HEADING_RE, Diag, content_words, find_key_line,
                     has_tab_indent, match_resource, norm, parse_block,
                     path_match, run_target, split_frontmatter,
                     yaml_unsafe_values)

ROOT_MARKER = "SKILL.md"
MAX_ROOT_DEPTH = 4


class Document:
    """One parsed file: header, body layout, contract, and flow trees."""

    def __init__(self, path, fragment):
        self.path = Path(path)
        self.fragment = fragment
        self.errors, self.warnings = [], []
        self.header, self.fm_lines = {}, []
        self.logics, self.order, self.trees, self.ast_diags = {}, [], {}, {}
        self.contract = None
        self.appendix_text = ""
        self.body_lines, self.body_first = [], 1
        self.readable = self._read()

    def _read(self):
        try:
            text = self.path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            self.errors.append(Diag(0, "F1", f"cannot read file {self.path}",
                                    "Check the path and save the file as UTF-8."))
            return False
        fm_lines, self.body_lines, self.body_first = split_frontmatter(text)
        if fm_lines is None:
            if not self.fragment:
                self.errors.append(Diag(1, "F1", "missing frontmatter block",
                                        "Start the file with --- YAML frontmatter."))
        else:
            self.fm_lines = fm_lines
            for idx, raw in enumerate(fm_lines):
                if raw.strip() and has_tab_indent(raw):
                    self.errors.append(Diag(idx + 2, "F1", "tab indentation is not allowed",
                                            "Indent frontmatter with spaces."))
            for idx, raw in enumerate(fm_lines):
                for member in yaml_unsafe_values(raw):
                    self.errors.append(Diag(idx + 2, "F1",
                                            f"unquoted {member!r} inside an inline collection is not valid YAML; hosts drop the header",
                                            f"Quote it: \"{member}\"."))
            parsed, _ = parse_block(list(fm_lines), 0, 0)
            if not isinstance(parsed, dict):
                self.errors.append(Diag(1, "F1", "frontmatter malformed",
                                        "Fix indentation and key: value shapes."))
            elif not self.fragment:
                self.header = parsed
        if self.header:
            check_schema(self.header, self.fm_lines, self.errors, self.warnings)
        self.logics, self.order, contract, self.appendix_text, fdiags = parse_fences(
            self.body_lines, self.body_first, fragment=self.fragment)
        self.errors.extend(fdiags)
        self.contract = read_contract(contract, self.errors, fragment=self.fragment)
        for flow, block in self.logics.items():
            diags0 = []
            self.trees[flow] = build_tree(block["stmts"], diags0)
            self.ast_diags[flow] = diags0
        return True

    @property
    def produces(self):
        if self.fragment:
            return None
        return set((self.header.get("produces") or {}).keys()) if self.header else set()


def looks_like_fragment(path):
    """A file without a SkillWren header (`skill:` key) is read as a fragment."""
    try:
        fm_lines, _, _ = split_frontmatter(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError):
        return True
    if fm_lines is None:
        return True
    return not any(re.match(r"skill\s*:", line) for line in fm_lines)


class Workspace:
    """Resolves and caches documents named by cross-file runs."""

    def __init__(self):
        self.docs = {}
        self._mutates, self._guarantees = {}, {}
        self._loading = set()

    def document(self, path, fragment=None):
        key = Path(path).resolve()
        if key not in self.docs:
            if fragment is None:
                fragment = looks_like_fragment(key)
            self.docs[key] = Document(key, fragment)
        return self.docs[key]

    def resolve_path(self, doc, rel):
        """Look for rel beside the file, then in each parent up to the skill
        root (the nearest directory holding SKILL.md)."""
        base = doc.path.parent
        for _ in range(MAX_ROOT_DEPTH + 1):
            candidate = base / rel
            if candidate.is_file():
                return candidate
            if (base / ROOT_MARKER).is_file() or base.parent == base:
                break
            base = base.parent
        return None

    def external(self, doc, flow, rel):
        """{error, returned, mutates, doc} for a cross-file run target."""
        found = self.resolve_path(doc, rel)
        if found is None:
            return {"error": f"cannot resolve {rel!r}"}
        callee = self.document(found)
        if not callee.readable:
            return {"error": f"cannot read {rel!r}"}
        if flow not in callee.trees:
            return {"error": f"{rel!r} has no logic block for flow {flow!r}"}
        if (callee.path, flow) in self._loading:
            return {"error": f"run cycle through {rel!r}"}
        returned, _ = collect_flow_facts(callee.trees[flow], callee.produces)
        return {"error": None, "returned": returned,
                "mutates": self.mutates(callee, flow), "doc": callee}

    def mutates(self, doc, flow):
        """True when the flow, or anything it runs, writes, saves, or executes."""
        key = (doc.path, flow)
        if key in self._mutates:
            return self._mutates[key]
        if key in self._loading:
            return False  # cycle: reported by the caller as R3
        self._loading.add(key)
        try:
            root = doc.trees[flow]
            result = direct_mutation(root)
            for node in walk(root):
                if result:
                    break
                rt = run_target(node.text) if node.kind == "action" and node.data == "run" else None
                if not rt:
                    continue
                target, rel = rt
                if rel is not None:
                    ext = self.external(doc, target, rel)
                    result = not ext["error"] and ext["mutates"]
                elif "." not in target and target in doc.trees:
                    result = self.mutates(doc, target)
        finally:
            self._loading.discard(key)
        self._mutates[key] = result
        return result

    def guarantee(self, doc, flow, pattern):
        """True when every returning path of flow completes pattern."""
        key = (doc.path, flow, norm(pattern))
        if key in self._guarantees:
            return self._guarantees[key]
        if key in self._loading:
            return False
        self._loading.add(key)
        try:
            root = doc.trees[flow]
            succ, _ = build_cfg(root, None, None)
            reach = reachable_nodes(root, succ)
            preds = predecessors(reach, succ)
            result = guarantees(root, reach, preds, pattern,
                                lambda node, pat: self.run_guarantee(doc, node, pat))
        finally:
            self._loading.discard(key)
        self._guarantees[key] = result
        return result

    def run_guarantee(self, doc, node, pattern):
        rt = run_target(node.text)
        if not rt:
            return False
        target, rel = rt
        if rel is not None:
            found = self.resolve_path(doc, rel)
            if found is None:
                return False
            callee = self.document(found)
            return target in callee.trees and self.guarantee(callee, target, pattern)
        if "." not in target and target in doc.trees:
            return self.guarantee(doc, target, pattern)
        return False


def _flow_mutates(doc, workspace):
    """Original same-file propagation plus resolved cross-file callees."""
    direct = {flow: direct_mutation(root) for flow, root in doc.trees.items()}
    for flow, root in doc.trees.items():
        if direct[flow]:
            continue
        for node in walk(root):
            rt = run_target(node.text) if node.kind == "action" and node.data == "run" else None
            if rt and rt[1] is not None:
                ext = workspace.external(doc, rt[0], rt[1])
                if not ext["error"] and ext["mutates"]:
                    direct[flow] = True
                    break
    calls = {flow: collect_flow_facts(root, doc.produces)[1] for flow, root in doc.trees.items()}
    flow_mutates = dict(direct)
    for _ in range(len(doc.trees) + 1):
        for flow, edges in calls.items():
            if not flow_mutates[flow] and any(flow_mutates.get(t, False) for _, t in edges):
                flow_mutates[flow] = True
    return flow_mutates


def _externals(doc, workspace):
    out = {}
    for root in doc.trees.values():
        for node in walk(root):
            rt = run_target(node.text) if node.kind == "action" and node.data == "run" else None
            if rt and rt[1] is not None and rt not in out:
                out[rt] = workspace.external(doc, rt[0], rt[1])
    return out


def _check_flow_set(doc, errors):
    flows_hdr = doc.header.get("flows") if isinstance(doc.header.get("flows"), list) else []
    for f in flows_hdr:
        if f not in doc.logics:
            errors.append(Diag(find_key_line(doc.fm_lines, "flows"), "F3",
                               f"header flow {f!r} has no logic fence",
                               "Add the fence or drop the flow."))
    for f in doc.logics:
        if f not in flows_hdr:
            errors.append(Diag(doc.logics[f]["header_line"], "F3",
                               f"flow {f!r} missing from header flows",
                               "Declare it in flows:."))


def _check_requires(doc, infos, errors):
    requires = doc.header.get("requires") if isinstance(doc.header.get("requires"), dict) else {}
    for flow in requires:
        if flow not in doc.logics:
            errors.append(Diag(find_key_line(doc.fm_lines, "requires"), "R1",
                               f"requires entry for unknown flow {flow!r}",
                               "Name a declared flow."))
    for flow, info in infos.items():
        got = [norm(c) for c in info["leading"]]
        if flow not in requires:
            if got:
                errors.append(Diag(doc.logics[flow]["header_line"], "R1",
                                   f"flow {flow!r} leading requires missing from header requires",
                                   "Duplicate them exactly."))
        elif [norm(c) for c in requires[flow]] != got:
            errors.append(Diag(doc.logics[flow]["header_line"], "R1",
                               f"header requires for {flow!r} mismatches the flow's leading requires",
                               "Copy them exactly (labels and blanks aside)."))


def _check_effects(doc, infos, errors, warnings):
    resources, fm_lines = doc.contract.resources, doc.fm_lines
    cov_r = set().union(*[i["covered_reads"] for i in infos.values()]) if infos else set()
    cov_w = set().union(*[i["covered_writes"] for i in infos.values()]) if infos else set()
    effects = doc.header.get("effects") if isinstance(doc.header.get("effects"), dict) else {}

    def entries(section):
        value = effects.get(section, [])
        return value if isinstance(value, list) else []

    def covered(resource, section_entries):
        return any(e == resource or path_match(e, resources[resource].get("path", ""))
                   for e in section_entries)

    reads, creates, mutates = entries("reads"), entries("creates"), entries("mutates")
    for r in sorted(cov_r):
        if not covered(r, reads):
            errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                               f"resource {r!r} read but uncovered by effects.reads",
                               "Add a reads entry."))
    for r in sorted(cov_w):
        if not covered(r, creates + mutates):
            errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                               f"resource {r!r} written but uncovered by effects.creates/mutates",
                               "Add a creates or mutates entry."))
    cov_x = set().union(*[i.get("covered_execs", set()) for i in infos.values()]) if infos else set()
    for r in sorted(cov_x):
        if not covered(r, entries("executes")):
            errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                               f"resource {r!r} executed but uncovered by effects.executes",
                               "Add an executes entry."))
    reported = set()
    for info in infos.values():
        both = set(info.get("literal_reads", [])) & set(info.get("literal_writes", []))
        for r, target in sorted(both):
            if (r, target) in reported:
                continue
            reported.add((r, target))
            if not covered(r, mutates):
                errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                                   f"resource {r!r} is read and written at {target!r};"
                                   " declare it under mutates",
                                   "Move the entry from creates to mutates."))
    for section in ("reads", "creates", "mutates", "executes"):
        if not isinstance(effects.get(section, []), list):
            continue
        for e in effects.get(section, []):
            if not match_resource(e, resources):
                warnings.append(Diag(find_key_line(fm_lines, "effects"), "W6",
                                     f"effects entry {e!r} matches no resource",
                                     "Declare the resource or drop the entry."))


def _check_authority_coverage(doc, infos, warnings):
    fm_lines = doc.fm_lines
    authority = doc.header.get("authority") if isinstance(doc.header.get("authority"), dict) else {}
    may = authority.get("system-may", []) if isinstance(authority.get("system-may"), list) else []
    decide = authority.get("user-decides", []) if isinstance(authority.get("user-decides"), list) else []
    texts = [t for i in infos.values() for t in i["texts"]]
    for entry in may:
        if not any(len(content_words(entry) & content_words(t)) >= 2 for t in texts):
            warnings.append(Diag(find_key_line(fm_lines, "authority"), "W2",
                                 f"system-may entry {entry!r} never exercised",
                                 "Use it in a flow or drop it."))
    asks_all = [(ln, t) for i in infos.values() for ln, t in i["asks"]]
    req_users = [t for i in infos.values() for t in i["req_users"]]
    cover_lines = [t for i in infos.values() for t in i.get("all_asks", [])] + req_users
    for ln, text in asks_all:
        if not any(len(content_words(text) & content_words(e)) >= 2 for e in decide):
            warnings.append(Diag(ln, "W3", "decision ask maps to no user-decides entry",
                                 "Share two content words with an entry."))
    first_header = doc.logics[doc.order[0]]["header_line"] if doc.order else 1
    for e in decide:
        if not any(len(content_words(e) & content_words(t)) >= 2 for t in cover_lines):
            warnings.append(Diag(first_header, "W3",
                                 f"user-decides entry {e!r} never exercised",
                                 "Exercise it in a flow or drop it."))


def _check_guidance(doc, infos, warnings):
    if not doc.fragment and any(i["has_generate"] for i in infos.values()) \
            and not APPENDIX_HEADING_RE.search(doc.appendix_text):
        gen_line = min([i.get("gen_line", 10 ** 9) for i in infos.values() if i["has_generate"]])
        warnings.append(Diag(gen_line if gen_line < 10 ** 9 else 1, "W4",
                             "creative step without appendix guidance",
                             "Add a ## Appendix section for generate steps."))
    # W12: every apply spec should be defined somewhere in the guidance text
    # (one list item or paragraph containing all of its content words).
    units = [content_words(u) for u in
             re.split(r"\n\s*\n|\n(?=\s*[-*] )", doc.appendix_text or "")]
    for flow in doc.order:
        for ln, _ind, text in doc.logics[flow]["stmts"]:
            if not text.startswith("apply "):
                continue
            spec = re.split(r"\s+(?:with|as)\s+", text[6:], maxsplit=1)[0]
            words = content_words(spec)
            if words and not any(words <= u for u in units):
                warnings.append(Diag(ln, "W12", f"apply spec {spec!r} has no appendix anchor",
                                     "Define it in the appendix, e.g. a step-meanings list item."))


def _check_unused(infos, warnings):
    for info in infos.values():
        for var, ln in info["binds"].items():
            if var not in info["reads"]:
                warnings.append(Diag(ln, "W5", f"binding {var!r} never referenced",
                                     "Use it or drop the `as`."))


def _check_recursion(infos, errors):
    edge_line = {}
    for flow, info in infos.items():
        for ln, tgt in info["edges"]:
            edge_line.setdefault((flow, tgt), ln)
    color = {f: 0 for f in infos}

    def visit(u):
        color[u] = 1
        for _, v in infos[u]["edges"]:
            if v not in color:
                continue
            if color[v] == 1:
                return (u, v)
            if color[v] == 0:
                hit = visit(v)
                if hit:
                    return hit
        color[u] = 2
        return None

    for f in infos:
        if color[f] == 0:
            hit = visit(f)
            if hit:
                u, v = hit
                errors.append(Diag(edge_line[(u, v)], "L2", f"run cycle {u} -> {v}",
                                   "Break the recursion."))
                break


def linked_documents(doc, workspace):
    """The document plus every file reachable through cross-file runs."""
    seen, stack, out = {doc.path.resolve()}, [doc], [doc]
    while stack:
        current = stack.pop()
        for root in current.trees.values():
            for node in walk(root):
                rt = run_target(node.text) if node.kind == "action" and node.data == "run" else None
                if not rt or rt[1] is None:
                    continue
                found = workspace.resolve_path(current, rt[1])
                if found is None or found.resolve() in seen:
                    continue
                seen.add(found.resolve())
                callee = workspace.document(found)
                out.append(callee)
                stack.append(callee)
    return out


def anchor_classes(doc, workspace):
    """Per order rule: the evidence classes of statements matching its earlier step,
    in this file and in files it runs."""
    steps = [step for linked in linked_documents(doc, workspace)
             for root in linked.trees.values() for step in classify(root)["steps"]]
    return [(rule, sorted({cls for node, cls in steps if matches(rule.first, node.text)}))
            for rule in doc.contract.order]


def _check_evidence_anchors(doc, workspace, warnings):
    """W15: an order rule whose earlier step is only ever the model's own
    judgment is cheap talk; nothing outside the model can observe it."""
    for rule, classes in anchor_classes(doc, workspace):
        if classes and set(classes) <= {"self"}:
            warnings.append(Diag(rule.line, "W15",
                                 f"order rule rests on self-report: every statement matching"
                                 f" {rule.first!r} is the model's own judgment",
                                 "Anchor it to something observable: `verify ... from <exec result>`,"
                                 " an exec, a written artifact, or a user decision."))


def _check_order_coverage(doc, infos, warnings):
    seen = set().union(*[i.get("order_seen", set()) for i in infos.values()]) if infos else set()
    for k, rule in enumerate(doc.contract.order):
        if k not in seen:
            warnings.append(Diag(rule.line, "W13",
                                 f"order rule never applies: no statement starts with {rule.then!r}",
                                 "Fix the pattern so it matches the later statement, or drop the rule."))


def _check_budget(doc, errors):
    budget = doc.header.get("budget") if isinstance(doc.header.get("budget"), dict) else {}

    def cap(key):
        try:
            return int(budget.get(key, -1))
        except (TypeError, ValueError):
            return -1

    hcap, bcap = cap("header"), cap("body")
    ht = math.ceil(len("\n".join(doc.fm_lines)) / 4)
    bt = math.ceil(len("\n".join(doc.body_lines)) / 4)
    if hcap > 0 and ht > hcap:
        errors.append(Diag(find_key_line(doc.fm_lines, "budget"), "B1",
                           f"header ~{ht} tokens over budget {hcap} (approx ceil(chars/4))",
                           "Trim prose values."))
    if bcap > 0 and bt > bcap:
        errors.append(Diag(doc.body_first, "B1",
                           f"body ~{bt} tokens over budget {bcap} (approx ceil(chars/4))",
                           "Compress flows or split the skill."))


def analyze_document(doc, workspace):
    """Run every check for one parsed document. Returns (errors, warnings, infos)."""
    errors, warnings = list(doc.errors), list(doc.warnings)
    if not doc.readable:
        return errors, warnings, {}
    # Preserve independent fence diagnostics, but do not run semantic passes
    # against a header whose container/type invariants failed validation.
    if any(diag.rule == "F1" for diag in errors):
        return errors, warnings, {}
    if doc.header:
        _check_flow_set(doc, errors)
    if doc.fragment and not doc.logics:
        warnings.append(Diag(1, "W14", "no logic block; nothing was checked",
                             "Add a ```logic block, or skip this file."))
    callee_out = {flow: collect_flow_facts(root, doc.produces)[0]
                  for flow, root in doc.trees.items()}
    external = _externals(doc, workspace)
    flow_mutates = _flow_mutates(doc, workspace)
    ctx = {"header": doc.header, "resources": doc.contract.resources,
           "nevers": doc.contract.nevers, "flows": list(doc.logics),
           "callee_out": callee_out, "flow_mutates": flow_mutates,
           "fragment": doc.fragment, "inputs": doc.contract.inputs,
           "external": external, "order": doc.contract.order,
           "run_guarantees": lambda node, pat: workspace.run_guarantee(doc, node, pat)}
    infos = {}
    for flow, block in doc.logics.items():
        errs, warns, info = analyze_flow(flow, doc.trees[flow], block["header_line"], ctx)
        errors.extend(doc.ast_diags[flow])
        errors.extend(errs)
        warnings.extend(warns)
        infos[flow] = info
    if doc.header:
        _check_requires(doc, infos, errors)
    if not doc.fragment:
        returned = set().union(*[i["returned"] for i in infos.values()]) if infos else set()
        for p in sorted(doc.produces - returned):
            errors.append(Diag(find_key_line(doc.fm_lines, "produces"), "R2",
                               f"produces entry {p!r} never returned",
                               "Return it from at least one flow."))
    if doc.header:
        _check_effects(doc, infos, errors, warnings)
        _check_authority_coverage(doc, infos, warnings)
    _check_guidance(doc, infos, warnings)
    _check_unused(infos, warnings)
    _check_recursion(infos, errors)
    _check_order_coverage(doc, infos, warnings)
    _check_evidence_anchors(doc, workspace, warnings)
    if doc.header:
        _check_budget(doc, errors)
    errors.sort(key=lambda d: d.line)
    warnings.sort(key=lambda d: d.line)
    return errors, warnings, infos


def validate_file(path, fragment=False, workspace=None):
    """(errors, warnings) for one file in skill layout, or fragment layout."""
    workspace = workspace or Workspace()
    doc = Document(path, fragment)
    workspace.docs.setdefault(doc.path.resolve(), doc)
    errors, warnings, _ = analyze_document(doc, workspace)
    return errors, warnings


def validate_fragment(path, workspace=None):
    return validate_file(path, fragment=True, workspace=workspace)


def audit(path, fragment=True):
    """Verifier-facing view: every gate's evidence class, every branch's
    controller, and each order rule's anchor classes (`check --audit`)."""
    workspace = Workspace()
    doc = workspace.document(path, fragment)
    flows = {}
    for flow, root in doc.trees.items():
        facts = classify(root)
        flows[flow] = {"gates": facts["gates"], "branches": facts["branches"]}
    return {"flows": flows, "rules": anchor_classes(doc, workspace)}


def summarize(path, fragment=True):
    """Per-flow inputs, writes, and runs, for reviewing what a fragment touches."""
    workspace = Workspace()
    doc = Document(path, fragment)
    _, _, infos = analyze_document(doc, workspace)
    return {flow: {"inputs": info.get("inputs", []),
                   "writes": sorted(set(info.get("writes", []))),
                   "runs": info.get("runs", [])}
            for flow, info in infos.items()}


def _triggers(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return [], 1
    fm_lines, _, _ = split_frontmatter(text)
    if fm_lines is None:
        return [], 1
    parsed, _ = parse_block(list(fm_lines), 0, 0)
    if not isinstance(parsed, dict):
        return [], 1
    owns = parsed.get("owns-when", [])
    return ([item for item in owns if isinstance(item, str)] if isinstance(owns, list) else [],
            find_key_line(fm_lines, "owns-when"))


def validate_files(paths, fragment=False):
    workspace = Workspace()
    result = {p: validate_file(p, fragment=fragment, workspace=workspace) for p in paths}
    if fragment:
        return result
    trigs = {p: _triggers(p) for p in paths}
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            a, b = paths[i], paths[j]
            ta, la = trigs[a]
            tb, lb = trigs[b]
            hit = any(norm(x) == norm(y) or len(content_words(x) & content_words(y)) >= 3
                      for x in ta for y in tb)
            if hit:
                for p, ln, other in ((a, la, b), (b, lb, a)):
                    result[p][1].append(Diag(ln, "W1", f"owns-when trigger overlaps {other}",
                                             "Differentiate the triggers."))
    return result
