"""SkillWren v0.4 validator: static checks for logic-first skills.

Single-file, stdlib-only. Usage: skillwren check <file>...
(or: python -m skillwren check <file>...)

Rule IDs (spec Section 13):
  Errors: F1 frontmatter/schema, F2 fences/contract/body-order,
    F3 flow/fence set, V1 vocabulary, R1 requires match, R2 returns,
    R3 run target, R4 required-input gates, U1 unbound reference,
    E1 effect target, E2 effect coverage, E3 immutable write,
    E4 impure apply, A1 allow/never, A2 ask/confirm structure,
    L1 label/loop, L2 recursion, L3 retry ownership,
    O1 otherwise/block structure, B1 budget, M1 mutation before ask.
  Warnings: W1 trigger overlap, W2 system-may, W3 ask mapping, W4 appendix,
    W5 write-never-read, W6 effects unmatched, W7 unknown field,
    W8 foreign run (unverified effect boundary),
    W9 otherwise fall-through, W10 unreachable code.

Token counts use ceil(chars/4), labeled approximate (spec Section 10
fallback; used always in v0.4 since tiktoken is optional).

Known limitations: same-skill run argument VALUES are checked for
boundness, not full type conformance (no dataflow type inference);
interpolated/wildcard paths are exempt from the create/mutate overlap
rule; cross-skill runs are an unverified effect boundary (W8).
"""
import math
import re
import sys
from collections import namedtuple
from pathlib import Path

Diag = namedtuple("Diag", ["line", "rule", "msg", "fix"])

FORMAT_VERSION = (0, 4)

STOPWORDS = {"a", "an", "the", "to", "of", "and", "or", "for", "with",
             "on", "in", "please"}
ACTIONS = {"open", "read", "write", "save", "show", "ask", "generate",
           "apply", "run", "return", "abort", "discard"}
BRANCH = {"if", "unless", "when"}
GATES = {"require", "verify", "allow"}
REQUIRED_KEYS = {"skill", "description", "version", "purpose", "accepts",
                 "produces", "owns-when", "requires", "flows", "authority",
                 "effects", "risk", "cost", "budget"}
KNOWN_KEYS = REQUIRED_KEYS | {"name"}
BASE_TYPES = {"Text", "Number", "Boolean", "Path", "Artifact", "Theme",
              "ThemeSpec", "Any"}
ACCESS_VALUES = {"read", "create", "read+create"}
RESOURCE_KEYS = {"path", "access", "immutable"}
VAR_ONLY = re.compile(r"[A-Za-z_][\w-]*\Z")
INTERP_RE = re.compile(r"\{([^{}]+)\}")
AS_RE = re.compile(r"\bas\s+(\S+)\s*$")
FROM_RE = re.compile(r"\bfrom\s+(.+?)(?:\s+as\s+\S+)?\s*$")
WITH_RE = re.compile(r"\bwith\s+(.+?)(?:\s+as\s+\S+)?\s*$")
ASSIGN_RE = re.compile(r"^([A-Za-z_][\w-]*)\s*=\s*(\S.*)$")
STRICT_OPEN_RE = re.compile(r"^```(logic|contract)\s*$")
KEBAB_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*\Z")
VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?\Z")
APPENDIX_HEADING_RE = re.compile(r"^#{1,6}\s+.*appendix",
                                 re.IGNORECASE | re.MULTILINE)


def content_words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower())
            if w not in STOPWORDS}


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def split_top_commas(s):
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def parse_inline_list(s):
    s = s.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return None
    inner = s[1:-1].strip()
    if not inner:
        return []
    return [strip_quotes(p) for p in split_top_commas(inner)]


def parse_inline_map(s):
    s = s.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None
    inner = s[1:-1].strip()
    if not inner:
        return {}
    out = {}
    for part in split_top_commas(inner):
        if ":" not in part:
            return None
        k, v = part.split(":", 1)
        out[k.strip()] = strip_quotes(v)
    return out


def parse_scalar(s):
    s = s.strip()
    if s.startswith("["):
        v = parse_inline_list(s)
        return v if v is not None else s
    if s.startswith("{"):
        v = parse_inline_map(s)
        return v if v is not None else s
    return strip_quotes(s)


def parse_block(lines, i, indent):
    """Parse an indented map/list block. Returns (obj, next_i) or (None, i)."""
    obj, n = None, len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.strip().startswith("#"):
            i += 1
            continue
        ind = len(raw) - len(raw.lstrip(" "))
        if ind < indent:
            break
        if ind > indent:
            return None, i
        text = raw.strip()
        if text.startswith("- "):
            if obj is None:
                obj = []
            if not isinstance(obj, list):
                return None, i
            obj.append(parse_scalar(text[2:]))
            i += 1
        elif ":" in text:
            if obj is None:
                obj = {}
            if not isinstance(obj, dict):
                return None, i
            k, v = text.split(":", 1)
            v = v.strip()
            if v:
                obj[k.strip()] = parse_scalar(v)
                i += 1
            else:
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j >= n:
                    return None, i
                child_ind = len(lines[j]) - len(lines[j].lstrip(" "))
                if child_ind <= indent:
                    return None, i
                child, i = parse_block(lines, j, child_ind)
                if child is None:
                    return None, i
                obj[k.strip()] = child
        else:
            return None, i
    return obj if obj is not None else {}, i


def split_frontmatter(text):
    """Returns (fm_lines, body_lines, body_first_lineno) or (None, lines, 1)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines, 1
    for j in range(1, len(lines)):
        if lines[j].strip() == "---":
            return lines[1:j], lines[j + 1:], j + 2
    return None, lines, 1


def find_key_line(fm_lines, key):
    for idx, raw in enumerate(fm_lines):
        if re.match(r"^" + re.escape(key) + r"\s*:", raw):
            return idx + 2
    return 1


def has_tab_indent(line):
    i = 0
    while i < len(line) and line[i] in " \t":
        if line[i] == "\t":
            return True
        i += 1
    return False


def valid_type(s):
    """Closed v0.4 type grammar: base | List<T> | Enum[a, b, ...]."""
    if s in BASE_TYPES:
        return True
    if s.startswith("List<") and s.endswith(">"):
        return valid_type(s[5:-1])
    if s.startswith("Enum[") and s.endswith("]"):
        elems = [p.strip() for p in split_top_commas(s[5:-1])]
        if not elems or any(not e for e in elems):
            return False
        if len(set(elems)) != len(elems):
            return False
        return all(not set(e) & set("[]<>{},") for e in elems)
    return False


def is_kebab(s):
    return isinstance(s, str) and bool(KEBAB_RE.match(s))


def parse_version(s):
    """Returns (major, minor) for `X.Y[.Z]`, else None."""
    if not isinstance(s, str):
        return None
    m = VERSION_RE.match(s.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


def classify_flow_line(text):
    """Kinds: label/otherwise/returnblock/returnto/foreach/branch/gate/
    action/assign/bareword/retry/misplaced-invariant/unknown."""
    if text == "otherwise:":
        return ("otherwise", None)
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


def seg_match(a, b):
    if a == b:
        return True
    wild = lambda s: "*" in s or ("{" in s and "}" in s)
    return wild(a) or wild(b)


def path_match(target, pattern):
    ta, pa = target.split("/"), pattern.split("/")
    return len(ta) == len(pa) and all(seg_match(x, y) for x, y in zip(ta, pa))


def match_resource(target, resources):
    if target in resources:
        return target
    for name, res in resources.items():
        if path_match(target, res.get("path", "")):
            return name
    return None


def strip_as_clause(rest):
    return re.sub(r"\s+as\s+\S+$", "", rest).strip()


def as_target(text):
    m = AS_RE.search(text)
    return m.group(1) if m else None


def from_source(text):
    m = FROM_RE.search(text)
    return m.group(1).strip() if m else None


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
    if parent.kind in ("root", "branch", "foreach", "otherwise"):
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
                              "Use only the v0.4 verb set."))
        elif kind == "misplaced-invariant":
            diags.append(Diag(ln, "V1", f"{data} outside the contract block",
                              "Move invariants to the contract block."))
        check_nesting(parent, node, diags)
    return root


END = object()  # sentinel: virtual flow exit


def next_after(node):
    parent = node.parent
    idx = parent.children.index(node)
    if idx + 1 < len(parent.children):
        return parent.children[idx + 1]
    if parent.kind == "root":
        return END
    return next_after(parent)


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
    if kind in ("branch", "foreach"):
        nxt = next_after(node)
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


def track_literal(info, key, resource, target):
    if "{" not in target and "}" not in target and "*" not in target:
        info[key].append((resource, target))


def collect_flow_facts(root, produces):
    """Pre-pass: returned names + same-skill call edges. No diags."""
    returned, calls = set(), []
    for node in walk(root):
        if node.kind == "action" and node.data == "return":
            m = re.fullmatch(r"return\s+(\S+)\s+as\s+([A-Za-z_][\w-]*)\s*",
                             node.text)
            if m and m.group(2) in produces:
                returned.add(m.group(2))
        elif node.kind == "action" and node.data == "run":
            m = re.fullmatch(r"run\s+(\S+)\s+with:", node.text)
            if m and "." not in m.group(1):
                calls.append((node.line, m.group(1)))
        elif node.kind == "assign" and node.parent.kind == "returnblock":
            m = ASSIGN_RE.match(node.text)
            if m and m.group(1) in produces:
                returned.add(m.group(1))
        elif node.kind == "bareword" and node.parent.kind == "returnblock":
            if node.text in produces:
                returned.add(node.text)
    return returned, calls


def analyze_flow(flow, root, header_line, ctx):
    """Returns (errors, warnings, info). ctx: header/resources/nevers/flows/
    callee_out/flow_mutates."""
    errors, warnings = [], []
    info = {"edges": [], "returned": set(), "asks": [], "req_users": [],
            "reads": set(), "binds": {}, "texts": [], "has_generate": False,
            "covered_reads": set(), "covered_writes": set(),
            "literal_reads": [], "literal_writes": []}
    header = ctx.get("header") or {}
    resources = ctx.get("resources", {})
    nevers = ctx.get("nevers", [])
    accepts = set((header.get("accepts") or {}).keys())
    produces = set((header.get("produces") or {}).keys())
    flows = set(ctx.get("flows", []))
    callee_out = ctx.get("callee_out", {})
    flow_mutates = ctx.get("flow_mutates", {})

    nodes = walk(root)
    succ, _ = build_cfg(root, errors, warnings)
    reach = reachable_nodes(root, succ)
    for node in nodes:
        if node not in reach:
            warnings.append(Diag(node.line, "W10", "unreachable statement",
                                 "Remove it or fix the control flow."))
    preds = predecessors(reach, succ)
    dom = dominators(root, succ, reach, preds)

    gen = {node: set() for node in nodes}
    kill = {node: set() for node in nodes}
    uses = {node: [] for node in nodes}

    def use(node, name, what):
        if name and VAR_ONLY.fullmatch(name):
            uses[node].append((name, what))

    ask_nodes, decision_asks = [], []
    confirm_user, confirm_bare = [], []
    apply_nodes, run_calls, direct_mutations = [], [], []
    pending_from = []

    for node in nodes:
        text = node.text
        kind, data = node.kind, node.data
        info["texts"].append(text)
        if kind in ("unknown", "misplaced-invariant"):
            continue  # V1 already emitted at build
        for var in INTERP_RE.findall(text):
            use(node, var.strip(), "interpolation")
        if kind == "label":
            continue  # duplicates handled in build_cfg
        if kind == "returnto":
            continue  # targets resolved in build_cfg
        if kind == "foreach":
            gen[node].add(data["var"])
            info["binds"].setdefault(data["var"], node.line)
            if VAR_ONLY.fullmatch(data["source"]):
                use(node, data["source"], "for-each source")
            continue
        if kind in ("branch", "otherwise", "retry"):
            continue
        if kind == "gate":
            rest = text[len(data):].strip()
            if data == "require" and rest.startswith("user "):
                info["req_users"].append(text)
                confirm_user.append(node)
            elif data == "require" and norm(rest) == "confirmation":
                confirm_bare.append(node)
            if data == "allow":
                if " when " not in text or not text.endswith(":"):
                    errors.append(Diag(node.line, "V1", "malformed allow",
                                       "Use `allow <action> when <condition>:`"
                                       " quoting one never invariant."))
                elif not any(len(content_words(text) & content_words(never)) >= 2
                             for never in nevers):
                    errors.append(Diag(node.line, "A1",
                                       "allow matches no never invariant",
                                       "Quote the invariant it narrows."))
            continue
        if kind == "returnblock":
            continue
        if kind == "assign":
            if node.parent.kind == "returnblock":
                m = ASSIGN_RE.match(text)
                name, val = m.group(1), m.group(2).strip()
                if name not in produces:
                    errors.append(Diag(node.line, "R2",
                                       f"return names undeclared produces entry {name!r}",
                                       "Return a skill produces entry."))
                else:
                    info["returned"].add(name)
                if VAR_ONLY.fullmatch(val):
                    use(node, val, "return value")
            elif is_run(node.parent):
                val = ASSIGN_RE.match(text).group(2).strip()
                if VAR_ONLY.fullmatch(val):
                    use(node, val, "run argument value")
            # elsewhere: V1 stray already emitted at build
            continue
        if kind == "bareword":
            if node.parent.kind == "returnblock":
                if text not in produces:
                    errors.append(Diag(node.line, "R2",
                                       f"return names undeclared produces entry {text!r}",
                                       "Return a skill produces entry."))
                else:
                    info["returned"].add(text)
                use(node, text, "return value")
            continue
        # kind == "action"
        verb, rest = data, text[len(data):].strip()
        if verb == "generate":
            info["has_generate"] = True
            info.setdefault("gen_line", node.line)
        tgt = as_target(text)
        if tgt and VAR_ONLY.fullmatch(tgt) \
                and verb not in ("save", "write", "return"):
            gen[node].add(tgt)
            info["binds"].setdefault(tgt, node.line)
        if tgt and VAR_ONLY.fullmatch(tgt):
            parent = node.parent
            while parent is not None and parent.kind != "root":
                if parent.kind == "foreach" and parent.data["var"] == tgt:
                    errors.append(Diag(node.line, "L1",
                                       f"mutation of for-each variable {tgt!r}",
                                       "Bind a new name instead."))
                    break
                parent = parent.parent
        if verb == "open":
            target = strip_as_clause(rest)
            if not target:
                errors.append(Diag(node.line, "E1", "open names no target",
                                   "Name a resource, path, or accepts entry."))
            else:
                name = match_resource(target, resources)
                if not name and target not in accepts:
                    errors.append(Diag(node.line, "E1",
                                       f"open target {target!r} matches no resource, path, or accepts entry",
                                       "Declare the resource or fix the name."))
                elif name:
                    info["covered_reads"].add(name)
                    track_literal(info, "literal_reads", name, target)
        elif verb == "read":
            src = from_source(text)
            if src is not None:
                name = match_resource(src, resources)
                if name:
                    info["covered_reads"].add(name)
                    track_literal(info, "literal_reads", name, src)
                elif VAR_ONLY.fullmatch(src):
                    pending_from.append((node, src))
                else:
                    errors.append(Diag(node.line, "E1",
                                       f"read source {src!r} matches no resource, path, or accepts entry",
                                       "Declare the resource or fix the name."))
            else:
                target = strip_as_clause(rest)
                if not target:
                    errors.append(Diag(node.line, "E1", "read names no target",
                                       "Name a path or use `read X from Y`."))
                else:
                    name = match_resource(target, resources)
                    if not name and target not in accepts:
                        errors.append(Diag(node.line, "E1",
                                           f"read target {target!r} matches no resource, path, or accepts entry",
                                           "Declare the resource or fix the name."))
                    elif name:
                        info["covered_reads"].add(name)
                        track_literal(info, "literal_reads", name, target)
        elif verb in ("write", "save"):
            direct_mutations.append(node)
            if verb == "write":
                m = WITH_RE.search(text)
                target = m.group(1).strip() if m else ""
                val = rest.split(" with ", 1)[0].strip()
            else:
                target = tgt or ""
                val = rest.rsplit(" as ", 1)[0].strip() if " as " in rest else ""
            if VAR_ONLY.fullmatch(val):
                use(node, val, f"{verb} value")
            name = match_resource(target, resources) if target else None
            if not target or (not name and target not in accepts):
                errors.append(Diag(node.line, "E1",
                                   f"{verb} target {target!r} matches no resource, path, or accepts entry",
                                   "Declare the resource or fix the path."))
            elif name:
                info["covered_writes"].add(name)
                track_literal(info, "literal_writes", name, target)
                if str(resources[name].get("immutable", "")).lower() == "true":
                    errors.append(Diag(node.line, "E3",
                                       f"{verb} to immutable resource {name!r}",
                                       "Write elsewhere or drop immutable:."))
        elif verb in ("show", "discard"):
            if VAR_ONLY.fullmatch(rest):
                use(node, rest, f"{verb} value")
            if verb == "discard" and VAR_ONLY.fullmatch(rest):
                kill[node].add(rest)
        elif verb == "ask":
            ask_nodes.append(node)
            info.setdefault("all_asks", []).append(text)
            if tgt and VAR_ONLY.fullmatch(tgt):
                pass  # input ask; binding recorded above
            else:
                decision_asks.append(node)
                info["asks"].append((node.line, text))
        elif verb == "apply":
            m = WITH_RE.search(text)
            target = m.group(1).strip() if m else ""
            if not (tgt and VAR_ONLY.fullmatch(tgt)):
                errors.append(Diag(node.line, "V1",
                                   "apply without `as` discards its result",
                                   "Bind the outcome with `as <name>`."))
            if VAR_ONLY.fullmatch(target) \
                    and not match_resource(target, resources):
                use(node, target, "apply target")
            apply_nodes.append((node, target))
        elif verb == "run":
            m = re.fullmatch(r"run\s+(\S+)\s+with:", text)
            if not m:
                errors.append(Diag(node.line, "V1", f"malformed run {text!r}",
                                   "Use `run <flow> with:` plus indented args."))
            else:
                target = m.group(1)
                if "." in target:
                    warnings.append(Diag(node.line, "W8",
                                         f"cross-skill run {target!r} is an unverified effect boundary",
                                         "Resolve it with a workspace validator;"
                                         " keep accepts aligned."))
                elif target not in flows:
                    errors.append(Diag(node.line, "R3",
                                       f"run target {target!r} is no flow in this file",
                                       "Run a declared flow."))
                else:
                    info["edges"].append((node.line, target))
                    gen[node].update(callee_out.get(target, set()))
                    run_calls.append((node, target))
        elif verb == "return":
            m = re.fullmatch(r"return\s+(\S+)\s+as\s+([A-Za-z_][\w-]*)\s*",
                             text)
            if not m:
                errors.append(Diag(node.line, "V1", f"malformed return {text!r}",
                                   "Use `return <binding> as <name>` or a `return:` block."))
            else:
                val, name = m.group(1), m.group(2)
                if VAR_ONLY.fullmatch(val):
                    use(node, val, "return value")
                if name not in produces:
                    errors.append(Diag(node.line, "R2",
                                       f"return names undeclared produces entry {name!r}",
                                       "Return a skill produces entry."))
                else:
                    info["returned"].add(name)
        elif verb == "abort":
            pass
        if verb != "read":
            src = from_source(text)
            if src and VAR_ONLY.fullmatch(src):
                use(node, src, "from source")

    # ---- definite-binding dataflow (must-analysis to a fixpoint) ----
    ever = set(accepts)
    for node in nodes:
        ever |= gen[node]
    entry = root.children[0] if root.children else None
    in_facts = {node: set(ever) for node in reach}
    out_facts = {node: set(ever) for node in reach}
    for _ in range(1000):
        changed = False
        for node in reach:
            ins = []
            for pred in preds[node]:
                if node.kind == "otherwise" and node.parent is pred \
                        and is_fallible(pred):
                    ins.append(in_facts[pred])  # fail edge: pre-gate facts
                else:
                    ins.append(out_facts[pred])
            if node is entry:
                ins.append(set(accepts))
            new_in = set.intersection(*ins) if ins else set(accepts)
            new_out = (new_in | gen[node]) - kill[node]
            if new_in != in_facts[node] or new_out != out_facts[node]:
                in_facts[node], out_facts[node] = new_in, new_out
                changed = True
        if not changed:
            break

    for node in reach:
        for name, what in uses[node]:
            info["reads"].add(name)
            if name not in in_facts[node]:
                if name in ever:
                    msg = f"{what} {name!r} may be unbound on some path"
                    fix = "Bind it on every path to this use."
                else:
                    msg = f"{what} {name!r} is not bound"
                    fix = "Bind it with `as` or declare it in accepts:."
                errors.append(Diag(node.line, "U1", msg, fix))
    for node, src in pending_from:
        if node in reach:
            info["reads"].add(src)
            resolve = in_facts[node]
        else:
            resolve = ever
        if src not in resolve:
            errors.append(Diag(node.line, "E1",
                               f"read source {src!r} matches no resource, path, or accepts entry",
                               "Declare the resource or fix the name."))
    for node, target in apply_nodes:
        if not target:
            continue
        resolve = in_facts[node] if node in reach else ever
        if match_resource(target, resources) and target not in resolve:
            errors.append(Diag(node.line, "E4",
                               f"apply target {target!r} is a resource, but apply is pure",
                               "Read it into a binding first, then apply to the binding."))

    # ---- leading requires (labels transparent, as in routing) ----
    leading = []
    for child in root.children:
        if child.kind == "label":
            continue
        if child.kind == "gate" and child.data == "require":
            leading.append(child.text[len("require"):].strip())
        else:
            break
    info["leading"] = leading

    # ---- R4: required inputs must be gated where they are used ----
    used = set()
    for node in reach:
        used.update(name for name, _ in uses[node])
    used.update(src for node, src in pending_from if node in reach)
    required_inputs = {name for name, entry in (header.get("accepts") or {}).items()
                       if isinstance(entry, dict) and entry.get("required") == "true"}
    for name in sorted(required_inputs):
        if name in used and norm(f"{name} exists") not in [norm(c) for c in leading]:
            errors.append(Diag(header_line, "R4",
                               f"required input {name!r} is used but never gated",
                               f"Add a leading `require {name} exists`."))

    # ---- R2: every reachable path ends in return or abort ----
    def ends_flow(node):
        return node.kind == "returnblock" \
            or (node.parent is not None and node.parent.kind == "returnblock") \
            or is_terminal(node)

    for node in reach:
        out = succ.get(node, [])
        if (not out or END in out) and not ends_flow(node):
            errors.append(Diag(node.line, "R2",
                               "flow falls off the end without return or abort",
                               "End every path with a return or abort."))
    if not any(node.kind == "returnblock" or is_terminal(node) for node in reach):
        errors.append(Diag(header_line, "R2",
                           "flow has no reachable return or abort",
                           "End the flow with a return or abort."))

    # ---- A2: decision ask/confirm structure (no fuzzy matching) ----
    for node in confirm_user:
        if node in reach and not any(d in dom[node] for d in decision_asks
                                     if d in reach):
            errors.append(Diag(node.line, "A2",
                               "user decision without a preceding ask",
                               "Ask the user before requiring their decision."))
    for node in decision_asks:
        if node in reach and not any(node in dom[c] for c in confirm_user + confirm_bare
                                     if c in reach):
            errors.append(Diag(node.line, "A2",
                               "decision ask without a following confirmation",
                               "Add `require confirmation` or `require user ...` after it."))
    for node in confirm_bare:
        if node in reach and not any(a in dom[node] for a in ask_nodes
                                     if a in reach):
            errors.append(Diag(node.line, "A2",
                               "confirmation without a preceding ask",
                               "Ask before requiring confirmation."))

    # ---- M1: no mutation on any path to a dismissible ask ----
    mut_nodes = {node for node in direct_mutations if node in reach}
    mut_nodes |= {node for node, target in run_calls
                  if node in reach and flow_mutates.get(target, False)}
    if mut_nodes:
        for ask in ask_nodes:
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
                stack.extend(p for p in preds.get(cur, ()) if p in reach)
            if hit is not None:
                errors.append(Diag(ask.line, "M1",
                                   f"ask after a mutation (line {hit.line}) breaks dismissal safety",
                                   "Move mutations after the confirmation, or remove the ask."))
    return errors, warnings, info


def check_schema(header, fm_lines, errors, warnings):
    missing = sorted(REQUIRED_KEYS - set(header.keys()))
    if missing:
        errors.append(Diag(1, "F1", f"frontmatter missing keys: {', '.join(missing)}",
                           "Add every required header field."))
    for key in sorted(set(header.keys()) - KNOWN_KEYS):
        warnings.append(Diag(find_key_line(fm_lines, key), "W7",
                             f"unknown frontmatter field {key!r}",
                             "Remove it or keep it if a tool needs it."))
    if header.get("name") and header.get("skill") \
            and header["name"] != header["skill"]:
        warnings.append(Diag(find_key_line(fm_lines, "name"), "W7",
                             "name should equal skill", "Align the two."))
    for key in ("skill", "description", "purpose"):
        if key in header and (not isinstance(header[key], str)
                              or not header[key].strip()):
            errors.append(Diag(find_key_line(fm_lines, key), "F1",
                               f"{key} must be a non-empty string",
                               "Fill it in."))
    if isinstance(header.get("skill"), str) and header["skill"].strip() \
            and not is_kebab(header["skill"]):
        errors.append(Diag(find_key_line(fm_lines, "skill"), "F1",
                           f"skill id {header['skill']!r} must be kebab-case",
                           "Use lowercase letters, digits, and hyphens."))
    if "version" in header:
        ver = parse_version(header["version"])
        if ver is None:
            errors.append(Diag(find_key_line(fm_lines, "version"), "F1",
                               f"version must look like 0.4, got {header['version']!r}",
                               "Use numeric major.minor[.patch]."))
        elif ver > FORMAT_VERSION:
            errors.append(Diag(find_key_line(fm_lines, "version"), "F1",
                               f"format version {header['version']} is newer than this validator"
                               f" ({FORMAT_VERSION[0]}.{FORMAT_VERSION[1]})",
                               "Upgrade SkillWren to check this skill."))
    auth = header.get("authority")
    if isinstance(auth, dict):
        for sub in ("user-decides", "system-decides", "system-may",
                    "system-must-not"):
            if sub not in auth:
                errors.append(Diag(find_key_line(fm_lines, "authority"), "F1",
                                   f"authority missing {sub}",
                                   "Add all four lists (empty allowed)."))
            elif not isinstance(auth[sub], list):
                errors.append(Diag(find_key_line(fm_lines, "authority"), "F1",
                                   f"authority.{sub} must be a list",
                                   "Use [a, b] form."))
    elif "authority" in header:
        errors.append(Diag(find_key_line(fm_lines, "authority"), "F1",
                           "authority must be a map",
                           "Use indented sub-lists."))
    eff = header.get("effects")
    if isinstance(eff, dict):
        for sub in ("reads", "creates", "mutates"):
            if sub not in eff:
                errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                                   f"effects missing {sub}",
                                   "Add reads/creates/mutates lists."))
            elif not isinstance(eff[sub], list):
                errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                                   f"effects.{sub} must be a list",
                                   "Use [a, b] form."))
    elif "effects" in header:
        errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                           "effects must be a map", "Use indented sub-lists."))
    for section in ("accepts", "produces"):
        val = header.get(section)
        if isinstance(val, dict):
            for name, entry in val.items():
                if not isinstance(entry, dict) or "type" not in entry:
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"{section}.{name} needs {{ type: ... }}",
                                       "Add the type."))
                elif not valid_type(str(entry["type"])):
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"{section}.{name} has unknown type {entry['type']!r}",
                                       "Use the closed v0.4 type set."))
                if section == "accepts" and isinstance(entry, dict) \
                        and "required" in entry \
                        and entry["required"] not in ("true", "false"):
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"accepts.{name}.required must be true or false",
                                       "Use `true` or `false`."))
        elif section in header:
            errors.append(Diag(find_key_line(fm_lines, section), "F1",
                               f"{section} must be a map",
                               "Use indented name: entries."))
    req = header.get("requires")
    if isinstance(req, dict):
        for flow, conds in req.items():
            if not is_kebab(flow):
                errors.append(Diag(find_key_line(fm_lines, "requires"), "F1",
                                   f"flow name {flow!r} must be kebab-case",
                                   "Use lowercase letters, digits, and hyphens."))
            if not isinstance(conds, list):
                errors.append(Diag(find_key_line(fm_lines, "requires"), "F1",
                                   f"requires.{flow} must be a list",
                                   "Use [condition, ...] form."))
    elif "requires" in header:
        errors.append(Diag(find_key_line(fm_lines, "requires"), "F1",
                           "requires must be a map", "Use indented flow: lists."))
    for section in ("flows", "owns-when"):
        if section in header and not isinstance(header[section], list):
            errors.append(Diag(find_key_line(fm_lines, section), "F1",
                               f"{section} must be a list", "Use - items or [a, b]."))
    if isinstance(header.get("flows"), list):
        for flow in header["flows"]:
            if not is_kebab(flow):
                errors.append(Diag(find_key_line(fm_lines, "flows"), "F1",
                                   f"flow name {flow!r} must be kebab-case",
                                   "Use lowercase letters, digits, and hyphens."))
    if "risk" in header and header["risk"] not in ("low", "medium", "high"):
        errors.append(Diag(find_key_line(fm_lines, "risk"), "F1",
                           f"risk must be low|medium|high, got {header['risk']!r}",
                           "Pick a valid level."))
    if "cost" in header and header["cost"] not in ("cheap", "moderate", "expensive"):
        errors.append(Diag(find_key_line(fm_lines, "cost"), "F1",
                           f"cost must be cheap|moderate|expensive, got {header['cost']!r}",
                           "Pick a valid level."))
    budget = header.get("budget")
    if isinstance(budget, dict):
        for sub in ("header", "body"):
            try:
                cap = int(budget.get(sub, "x"))
            except (TypeError, ValueError):
                errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                                   f"budget.{sub} must be an integer",
                                   "Use a token count."))
            else:
                if cap <= 0:
                    errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                                       f"budget.{sub} must be a positive integer",
                                       "Use a token count above zero."))
    elif "budget" in header:
        errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                           "budget must be a map", "Use { header: N, body: M }."))


def parse_fences(body_lines, first_lineno):
    """Returns (logics, order, contract, appendix_text, diags).

    Strict v0.4 rules: semantic fences are exactly ```logic / ```contract;
    the contract block precedes all logic blocks; no prose may sit between
    semantic blocks and no semantic block may follow appendix content.
    Lines before the first fence are an ignored preamble (titles).
    """
    logics, order, contract = {}, [], None
    blocks = []  # (kind, open_lineno, open_idx, content, close_idx)
    diags = []
    i, n = 0, len(body_lines)
    while i < n:
        raw = body_lines[i]
        lineno = first_lineno + i
        m = STRICT_OPEN_RE.match(raw)
        if m:
            info = m.group(1)
            open_idx = i
            i += 1
            content = []
            while i < n and body_lines[i].strip() != "```":
                content.append((first_lineno + i, body_lines[i]))
                i += 1
            if i >= n:
                diags.append(Diag(lineno, "F2", "unclosed fenced block",
                                  "Close it with ```."))
                break
            blocks.append((info, lineno, open_idx, content, i))
            i += 1
            continue
        stripped = raw.strip()
        if stripped.startswith("```"):
            if stripped == "```":
                diags.append(Diag(lineno, "F2", "stray closing fence",
                                  "Remove it or open a logic/contract block first."))
                i += 1
                continue
            ticks = len(stripped) - len(stripped.lstrip("`"))
            if ticks != 3:
                diags.append(Diag(lineno, "F2",
                                  "fence must be exactly three backticks",
                                  "Open semantic blocks with ```logic or ```contract."))
            else:
                diags.append(Diag(lineno, "F2",
                                  f"fence info string must be logic or contract,"
                                  f" got {stripped[3:].strip()!r}",
                                  "Relabel the fence (appendix code samples must avoid fences)."))
            i += 1
            while i < n and body_lines[i].strip() != "```":
                i += 1
            i += 1
            continue
        i += 1
    contract_count = 0
    for info, lineno, _open_idx, content, _close_idx in blocks:
        if info == "contract":
            contract_count += 1
            if contract_count > 1:
                diags.append(Diag(lineno, "F2", "duplicate contract block",
                                  "Keep exactly one contract block."))
            else:
                contract = {"line": lineno, "content": content}
            continue
        head = None
        for ln, raw in content:
            if raw.strip():
                head = (ln, raw.strip())
                break
        if head is None or not re.fullmatch(r"[A-Za-z][\w-]*:", head[1]):
            diags.append(Diag(lineno, "F2", "logic block must open with a `flowname:` header",
                              "Add the flow header as the first line."))
            continue
        flow = head[1][:-1]
        if not is_kebab(flow):
            diags.append(Diag(head[0], "F2", f"flow name {flow!r} must be kebab-case",
                              "Use lowercase letters, digits, and hyphens."))
        if flow in logics:
            diags.append(Diag(head[0], "F2", f"duplicate flow block {flow!r}",
                              "Merge or rename the flow."))
            continue
        stmts = []
        for ln, raw in content:
            if not raw.strip() or (ln == head[0] and raw.strip() == head[1]):
                continue
            if has_tab_indent(raw):
                diags.append(Diag(ln, "F2", "tab indentation is not allowed",
                                  "Indent with spaces."))
            stmts.append((ln, len(raw) - len(raw.lstrip(" ")), raw.strip()))
        logics[flow] = {"header_line": head[0], "stmts": stmts}
        order.append(flow)
    if blocks:
        covered = set()
        for _, _, open_idx, content, close_idx in blocks:
            covered.add(open_idx)
            covered.add(close_idx)
            for k in range(len(content)):
                covered.add(open_idx + 1 + k)
        first_open = min(b[2] for b in blocks)
        last_close = max(b[4] for b in blocks)
        appendix_idx = None
        for j in range(n):
            if j in covered or not body_lines[j].strip():
                continue
            if j < first_open:
                continue  # preamble: ignored
            if appendix_idx is None:
                appendix_idx = j
            if j < last_close:
                diags.append(Diag(first_lineno + j, "F2",
                                  "content between semantic blocks",
                                  "Move prose after the final fence."))
        for info, lineno, open_idx, _, _ in blocks:
            if appendix_idx is not None and open_idx > appendix_idx:
                diags.append(Diag(lineno, "F2",
                                  "semantic block after appendix began",
                                  "Keep contract and logic blocks before any prose."))
        contract_idx = next((b[2] for b in blocks if b[0] == "contract"), None)
        if contract_idx is not None:
            for info, lineno, open_idx, _, _ in blocks:
                if info == "logic" and open_idx < contract_idx:
                    diags.append(Diag(lineno, "F2",
                                      "contract block must precede logic blocks",
                                      "Move the contract block first."))
        last_end = last_close + 1
    else:
        last_end = 0
    appendix_text = "\n".join(body_lines[last_end:])
    return logics, order, contract, appendix_text, diags


def parse_contract(contract, diags):
    """Returns (resources, always, nevers). Appends F2 diags."""
    resources, always, nevers = {}, [], []
    if contract is None:
        diags.append(Diag(1, "F2", "missing contract block",
                          "Add one fenced contract block with resources/always/never."))
        return resources, always, nevers
    for ln, raw in contract["content"]:
        if raw.strip() and has_tab_indent(raw):
            diags.append(Diag(ln, "F2", "tab indentation is not allowed",
                              "Indent with spaces."))
    sections, current = {}, None
    for ln, raw in contract["content"]:
        if not raw.strip():
            continue
        ind = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if ind == 0 and text in ("resources:", "always:", "never:"):
            current = text[:-1]
            if current in sections:
                diags.append(Diag(ln, "F2", f"duplicate {text} section",
                                  "Keep one of each."))
            sections[current] = (ln, [])
        elif ind == 0:
            diags.append(Diag(ln, "F2", f"unexpected {text!r} in contract block",
                              "Only resources:/always:/never: live here."))
        elif current is None:
            diags.append(Diag(ln, "F2", "contract line outside any section",
                              "Place it under resources:/always:/never:."))
        else:
            sections[current][1].append((ln, ind, text))
    for need in ("resources", "always", "never"):
        if need not in sections:
            diags.append(Diag(contract["line"], "F2",
                              f"contract block missing {need}: section",
                              f"Add the {need}: section."))
    if all(s in sections for s in ("resources", "always", "never")):
        lines = [sections[s][0] for s in ("resources", "always", "never")]
        if lines != sorted(lines):
            diags.append(Diag(contract["line"], "F2",
                              "contract sections out of order",
                              "Use resources:, always:, never: in that order."))
    if "resources" in sections:
        current_res = None
        for ln, ind, text in sections["resources"][1]:
            if ind == 2 and text.endswith(":"):
                current_res = text[:-1]
                resources[current_res] = {"line": ln}
            elif current_res is not None and ":" in text:
                k, v = text.split(":", 1)
                resources[current_res][k.strip()] = strip_quotes(v)
            else:
                diags.append(Diag(ln, "F2", f"malformed resource line {text!r}",
                                  "Use `name:` then indented path:/access:."))
        for name, res in resources.items():
            if "path" not in res or "access" not in res:
                diags.append(Diag(res["line"], "F2",
                                  f"resource {name!r} needs path: and access:",
                                  "Add both keys."))
            for key in sorted(res):
                if key not in RESOURCE_KEYS | {"line"}:
                    diags.append(Diag(res["line"], "F2",
                                      f"resource {name!r} has unknown property {key!r}",
                                      "Use only path:, access:, immutable:."))
            if "access" in res and res["access"] not in ACCESS_VALUES:
                diags.append(Diag(res["line"], "F2",
                                  f"resource {name!r} access must be one of"
                                  f" read, create, read+create, got {res['access']!r}",
                                  "Use the canonical access value."))
            if "immutable" in res and res["immutable"] not in ("true", "false"):
                diags.append(Diag(res["line"], "F2",
                                  f"resource {name!r} immutable must be true or false",
                                  "Use `true` or `false`."))
    if "always" in sections:
        always = [t for _, _, t in sections["always"][1]]
    if "never" in sections:
        nevers = [t for _, _, t in sections["never"][1]]
    return resources, always, nevers


def validate_file(path):
    errors, warnings = [], []
    try:
        text = Path(path).read_text()
    except OSError:
        return [Diag(0, "F1", f"cannot read file {path}",
                     "Check the path.")], []
    fm_lines, body_lines, body_first = split_frontmatter(text)
    header = {}
    if fm_lines is None:
        errors.append(Diag(1, "F1", "missing frontmatter block",
                           "Start the file with --- YAML frontmatter."))
        fm_lines = []
    else:
        for idx, raw in enumerate(fm_lines):
            if raw.strip() and has_tab_indent(raw):
                errors.append(Diag(idx + 2, "F1",
                                   "tab indentation is not allowed",
                                   "Indent frontmatter with spaces."))
        parsed, _ = parse_block(list(fm_lines), 0, 0)
        if not isinstance(parsed, dict):
            errors.append(Diag(1, "F1", "frontmatter malformed",
                               "Fix indentation and key: value shapes."))
        else:
            header = parsed
    if header:
        check_schema(header, fm_lines, errors, warnings)
    logics, order, contract, appendix_text, fdiags = parse_fences(
        body_lines, body_first)
    errors.extend(fdiags)
    resources, always, nevers = parse_contract(contract, errors)
    flows_hdr = header.get("flows") if isinstance(header.get("flows"), list) else []
    if header:
        for f in flows_hdr:
            if f not in logics:
                errors.append(Diag(find_key_line(fm_lines, "flows"), "F3",
                                   f"header flow {f!r} has no logic fence",
                                   "Add the fence or drop the flow."))
        for f in logics:
            if f not in flows_hdr:
                errors.append(Diag(logics[f]["header_line"], "F3",
                                   f"flow {f!r} missing from header flows",
                                   "Declare it in flows:."))
    produces = set((header.get("produces") or {}).keys()) if header else set()
    trees, ast_diags = {}, {}
    for flow, block in logics.items():
        diags0 = []
        trees[flow] = build_tree(block["stmts"], diags0)
        ast_diags[flow] = diags0
    callee_out, call_edges = {}, {}
    for flow, root in trees.items():
        returned, calls = collect_flow_facts(root, produces)
        callee_out[flow] = returned
        call_edges[flow] = calls
    direct_mut = {}
    for flow, root in trees.items():
        succ0, _ = build_cfg(root, None, None)
        reach0 = reachable_nodes(root, succ0)
        direct_mut[flow] = any(node in reach0 and node.kind == "action"
                               and node.data in ("write", "save")
                               for node in walk(root))
    flow_mutates = dict(direct_mut)
    for _ in range(len(trees) + 1):
        for flow, calls in call_edges.items():
            if not flow_mutates[flow] and any(
                    flow_mutates.get(target, False) for _, target in calls):
                flow_mutates[flow] = True
    ctx = {"header": header, "resources": resources, "nevers": nevers,
           "flows": list(logics), "callee_out": callee_out,
           "flow_mutates": flow_mutates}
    infos = {}
    for flow, block in logics.items():
        errs, warns, info = analyze_flow(flow, trees[flow],
                                         block["header_line"], ctx)
        errors.extend(ast_diags[flow])
        errors.extend(errs)
        warnings.extend(warns)
        infos[flow] = info
    requires = header.get("requires") if isinstance(header.get("requires"), dict) else {}
    if header:
        for flow in requires:
            if flow not in logics:
                errors.append(Diag(find_key_line(fm_lines, "requires"), "R1",
                                   f"requires entry for unknown flow {flow!r}",
                                   "Name a declared flow."))
        for flow, info in infos.items():
            got = [norm(c) for c in info["leading"]]
            if flow not in requires:
                if got:
                    errors.append(Diag(logics[flow]["header_line"], "R1",
                                       f"flow {flow!r} leading requires missing from header requires",
                                       "Duplicate them exactly."))
            elif [norm(c) for c in requires[flow]] != got:
                errors.append(Diag(logics[flow]["header_line"], "R1",
                                   f"header requires for {flow!r} mismatches the flow's leading requires",
                                   "Copy them exactly (labels and blanks aside)."))
    returned = set().union(*[i["returned"] for i in infos.values()]) if infos else set()
    for p in sorted(produces - returned):
        errors.append(Diag(find_key_line(fm_lines, "produces"), "R2",
                           f"produces entry {p!r} never returned",
                           "Return it from at least one flow."))
    cov_r = set().union(*[i["covered_reads"] for i in infos.values()]) if infos else set()
    cov_w = set().union(*[i["covered_writes"] for i in infos.values()]) if infos else set()
    if header:
        effects = header.get("effects") if isinstance(header.get("effects"), dict) else {}
        reads = effects.get("reads", []) if isinstance(effects.get("reads"), list) else []
        creates = effects.get("creates", []) if isinstance(effects.get("creates"), list) else []
        mutates = effects.get("mutates", []) if isinstance(effects.get("mutates"), list) else []
        for r in sorted(cov_r):
            if not any(e == r or path_match(e, resources[r].get("path", "")) for e in reads):
                errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                                   f"resource {r!r} read but uncovered by effects.reads",
                                   "Add a reads entry."))
        for r in sorted(cov_w):
            if not any(e == r or path_match(e, resources[r].get("path", "")) for e in creates + mutates):
                errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                                   f"resource {r!r} written but uncovered by effects.creates/mutates",
                                   "Add a creates or mutates entry."))
        reported_overlap = set()
        for info in infos.values():
            read_lits = set(info.get("literal_reads", []))
            write_lits = set(info.get("literal_writes", []))
            for r, target in sorted(read_lits & write_lits):
                if (r, target) in reported_overlap:
                    continue
                reported_overlap.add((r, target))
                if not any(e == r or path_match(e, resources[r].get("path", ""))
                           for e in mutates):
                    errors.append(Diag(find_key_line(fm_lines, "effects"), "E2",
                                       f"resource {r!r} is read and written at {target!r};"
                                       " declare it under mutates",
                                       "Move the entry from creates to mutates."))
        for section in ("reads", "creates", "mutates"):
            entries = effects.get(section, [])
            if not isinstance(entries, list):
                continue
            for e in entries:
                if not match_resource(e, resources):
                    warnings.append(Diag(find_key_line(fm_lines, "effects"), "W6",
                                         f"effects entry {e!r} matches no resource",
                                         "Declare the resource or drop the entry."))
    if header:
        authority = header.get("authority") if isinstance(header.get("authority"), dict) else {}
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
                warnings.append(Diag(ln, "W3",
                                     "decision ask maps to no user-decides entry",
                                     "Share two content words with an entry."))
        first_header = logics[order[0]]["header_line"] if order else 1
        for e in decide:
            if not any(len(content_words(e) & content_words(t)) >= 2
                       for t in cover_lines):
                warnings.append(Diag(first_header, "W3",
                                     f"user-decides entry {e!r} never exercised",
                                     "Exercise it in a flow or drop it."))
    if any(i["has_generate"] for i in infos.values()) \
            and not APPENDIX_HEADING_RE.search(appendix_text):
        gen_line = min([i.get("gen_line", 10 ** 9) for i in infos.values()
                        if i["has_generate"]])
        warnings.append(Diag(gen_line if gen_line < 10 ** 9 else 1, "W4",
                             "creative step without appendix guidance",
                             "Add a ## Appendix section for generate steps."))
    for flow, info in infos.items():
        for var, ln in info["binds"].items():
            if var not in info["reads"]:
                warnings.append(Diag(ln, "W5", f"binding {var!r} never referenced",
                                     "Use it or drop the `as`."))
    graph = {flow: [t for _, t in info["edges"]] for flow, info in infos.items()}
    edge_line = {}
    for flow, info in infos.items():
        for ln, tgt in info["edges"]:
            edge_line.setdefault((flow, tgt), ln)
    color = {f: 0 for f in graph}

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

    for f in graph:
        if color[f] == 0:
            hit = visit(f)
            if hit:
                u, v = hit
                errors.append(Diag(edge_line[(u, v)], "L2",
                                   f"run cycle {u} -> {v}",
                                   "Break the recursion."))
                break
    if header:
        budget = header.get("budget") if isinstance(header.get("budget"), dict) else {}
        try:
            hcap = int(budget.get("header", -1))
        except (TypeError, ValueError):
            hcap = -1
        try:
            bcap = int(budget.get("body", -1))
        except (TypeError, ValueError):
            bcap = -1
        ht = math.ceil(len("\n".join(fm_lines)) / 4)
        bt = math.ceil(len("\n".join(body_lines)) / 4)
        if hcap > 0 and ht > hcap:
            errors.append(Diag(find_key_line(fm_lines, "budget"), "B1",
                               f"header ~{ht} tokens over budget {hcap} (approx ceil(chars/4))",
                               "Trim prose values."))
        if bcap > 0 and bt > bcap:
            errors.append(Diag(body_first, "B1",
                               f"body ~{bt} tokens over budget {bcap} (approx ceil(chars/4))",
                               "Compress flows or split the skill."))
    errors.sort(key=lambda d: d.line)
    warnings.sort(key=lambda d: d.line)
    return errors, warnings


def _triggers(path):
    try:
        text = Path(path).read_text()
    except OSError:
        return [], 1
    fm_lines, _, _ = split_frontmatter(text)
    if fm_lines is None:
        return [], 1
    parsed, _ = parse_block(list(fm_lines), 0, 0)
    if not isinstance(parsed, dict):
        return [], 1
    owns = parsed.get("owns-when", [])
    return (owns if isinstance(owns, list) else [],
            find_key_line(fm_lines, "owns-when"))


def validate_files(paths):
    result = {p: validate_file(p) for p in paths}
    trigs = {p: _triggers(p) for p in paths}
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            a, b = paths[i], paths[j]
            ta, la = trigs[a]
            tb, lb = trigs[b]
            hit = any(norm(x) == norm(y)
                      or len(content_words(x) & content_words(y)) >= 3
                      for x in ta for y in tb)
            if hit:
                for p, ln, other in ((a, la, b), (b, lb, a)):
                    errs, warns = result[p]
                    warns.append(Diag(ln, "W1",
                                      f"owns-when trigger overlaps {other}",
                                      "Differentiate the triggers."))
    return result


def main(argv):
    if len(argv) < 3 or argv[1] != "check":
        print("usage: skillwren check <file>...")
        return 2
    code = 0
    for path, (errors, warnings) in validate_files(argv[2:]).items():
        for d in sorted(errors, key=lambda x: x.line):
            print(f"{path}:{d.line}: error {d.rule}: {d.msg} -- {d.fix}")
        for d in sorted(warnings, key=lambda x: x.line):
            print(f"{path}:{d.line}: warning {d.rule}: {d.msg} -- {d.fix}")
        if errors:
            code = 1
    if code == 0:
        print("clean")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
