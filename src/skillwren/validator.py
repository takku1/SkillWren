"""SkillWren v0.3 validator: static checks for logic-first skills.

Single-file, stdlib-only. Usage: skillwren check <file>...
(or: python -m skillwren check <file>...)

Rule IDs (spec Section 13):
  Errors: F1 frontmatter/schema, F2 fences, F3 flow/fence set, V1 vocabulary,
    R1 requires match, R2 returns, R3 run target, U1 unbound reference,
    E1 effect target, E2 effect coverage, E3 immutable write, A1 allow/never,
    L1 label/loop, L2 recursion, B1 budget.
  Warnings: W1 trigger overlap, W2 system-may, W3 ask mapping, W4 appendix,
    W5 write-never-read, W6 effects unmatched, W7 unknown field,
    W8 foreign run.

Token counts use ceil(chars/4), labeled approximate (spec Section 10
fallback; used always in v0.3 since tiktoken is optional).

Known limitation: same-skill run argument VALUES are checked for boundness,
not full type conformance (no dataflow type inference in v0.3).
"""
import math
import re
import sys
from collections import namedtuple
from pathlib import Path

Diag = namedtuple("Diag", ["line", "rule", "msg", "fix"])

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
TYPE_RE = re.compile(r"^(Text|Number|Boolean|Path|Artifact|Theme|ThemeSpec|Any"
                     r"|List<.+?>|Enum\[[^\]]+\])$")
VAR_RE = re.compile(r"[A-Za-z_][\w-]*")
VAR_ONLY = re.compile(r"[A-Za-z_][\w-]*\Z")
INTERP_RE = re.compile(r"\{([^{}]+)\}")
AS_RE = re.compile(r"\bas\s+(\S+)\s*$")
FROM_RE = re.compile(r"\bfrom\s+(.+?)(?:\s+as\s+\S+)?\s*$")
WITH_RE = re.compile(r"\bwith\s+(.+?)(?:\s+as\s+\S+)?\s*$")
ASSIGN_RE = re.compile(r"^([A-Za-z_][\w-]*)\s*=\s*(\S.*)$")
RUN_RE = re.compile(r"run\s+(\S+)\s+with:$")
FENCE_RE = re.compile(r"^(`{3,})(\w*)\s*$")


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


def parse_fences(body_lines, first_lineno):
    """Returns (logics, contract, appendix_text, diags).

    logics: {flow: {"header_line": n, "stmts": [(lineno, indent, text)]}}.
    contract: list of (lineno, raw) or None.
    """
    logics, order, contract = {}, [], None
    contract_count, diags = 0, []
    i, n = 0, len(body_lines)
    last_end = 0
    while i < n:
        m = FENCE_RE.match(body_lines[i])
        if not m:
            i += 1
            continue
        info = m.group(2)
        lineno = first_lineno + i
        if info == "":
            diags.append(Diag(lineno, "F2", "stray closing fence",
                              "Remove it or open a logic/contract block first."))
            i += 1
            continue
        if info not in ("logic", "contract"):
            diags.append(Diag(
                lineno, "F2",
                f"fence info string must be logic or contract, got {info!r}",
                "Relabel the fence (appendix code samples must avoid fences)."))
            i += 1
            while i < n and not body_lines[i].strip().startswith("```"):
                i += 1
            i += 1
            last_end = i
            continue
        i += 1
        content = []
        while i < n and not body_lines[i].strip().startswith("```"):
            content.append((first_lineno + i, body_lines[i]))
            i += 1
        if i >= n:
            diags.append(Diag(lineno, "F2", "unclosed fenced block",
                              "Close it with ```."))
            break
        i += 1
        last_end = i
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
            diags.append(Diag(
                lineno, "F2", "logic block must open with a `flowname:` header",
                "Add the flow header as the first line."))
            continue
        flow = head[1][:-1]
        if flow in logics:
            diags.append(Diag(head[0], "F2", f"duplicate flow block {flow!r}",
                              "Merge or rename the flow."))
            continue
        stmts = []
        for ln, raw in content:
            if not raw.strip() or (ln == head[0] and raw.strip() == head[1]):
                continue
            stmts.append((ln, len(raw) - len(raw.lstrip(" ")), raw.strip()))
        logics[flow] = {"header_line": head[0], "stmts": stmts}
        order.append(flow)
    appendix_text = "\n".join(body_lines[last_end:])
    return logics, order, contract, appendix_text, diags


def parse_contract(contract, diags):
    """Returns (resources, always, nevers). Appends F2 diags."""
    resources, always, nevers = {}, [], []
    if contract is None:
        diags.append(Diag(1, "F2", "missing contract block",
                          "Add one fenced contract block with resources/always/never."))
        return resources, always, nevers
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
    if "always" in sections:
        always = [t for _, _, t in sections["always"][1]]
    if "never" in sections:
        nevers = [t for _, _, t in sections["never"][1]]
    return resources, always, nevers

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


def analyze_flow(flow, stmts, ctx):
    """Returns (errors, warnings, info). ctx: header/resources/nevers/flows."""
    errors, warnings = [], []
    info = {"labels": {}, "returntos": [], "edges": [], "returned": set(),
            "asks": [], "req_users": [], "reads": set(), "binds": {},
            "foreach": [], "texts": [], "has_generate": False,
            "covered_reads": set(), "covered_writes": set()}
    header = ctx.get("header") or {}
    resources = ctx.get("resources", {})
    nevers = ctx.get("nevers", [])
    accepts = set((header.get("accepts") or {}).keys())
    produces = set((header.get("produces") or {}).keys())
    flows = set(ctx.get("flows", []))
    bindings = set(accepts)

    def note_read(name):
        if name and VAR_ONLY.fullmatch(name):
            info["reads"].add(name)

    def known(name):
        return name in bindings or name in accepts or name in resources

    def check_bound(name, ln, what):
        if name and VAR_ONLY.fullmatch(name) and not known(name):
            errors.append(Diag(ln, "U1", f"{what} {name!r} is not bound",
                               "Bind it with `as` or declare it in accepts:."))

    def follows_run(idx):
        ind = stmts[idx][1]
        j = idx - 1
        while j >= 0 and stmts[j][1] == ind and \
                classify_flow_line(stmts[j][2])[0] == "assign":
            j -= 1
        if j < 0:
            return False
        ln2, ind2, text2 = stmts[j]
        return ind2 < ind and classify_flow_line(text2) == ("action", "run")

    base_ind = stmts[0][1] if stmts else 0
    returnblock_ind = None
    for idx, (ln, ind, text) in enumerate(stmts):
        info["texts"].append(text)
        if returnblock_ind is not None and ind <= returnblock_ind:
            returnblock_ind = None
        kind, data = classify_flow_line(text)
        if kind == "unknown":
            errors.append(Diag(ln, "V1", f"unknown statement {text!r}",
                               "Use only the v0.3 verb set."))
            continue
        if kind == "misplaced-invariant":
            errors.append(Diag(ln, "V1", f"{data} outside the contract block",
                               "Move invariants to the contract block."))
            continue
        for var in INTERP_RE.findall(text):
            var = var.strip()
            note_read(var)
            check_bound(var, ln, "interpolation")
        if kind == "label":
            if data in info["labels"]:
                errors.append(Diag(ln, "L1", f"duplicate label {data!r}",
                                   "Keep label names unique per flow."))
            else:
                info["labels"][data] = ln
            continue
        if kind == "returnto":
            info["returntos"].append((ln, data))
            continue
        if kind == "foreach":
            bindings.add(data["var"])
            info["binds"].setdefault(data["var"], ln)
            info["foreach"].append((ln, ind, data["var"]))
            src = data["source"]
            if VAR_ONLY.fullmatch(src):
                note_read(src)
                check_bound(src, ln, "for-each source")
            continue
        if kind in ("branch", "otherwise", "retry"):
            continue
        if kind == "gate":
            if data == "require" and text[len("require"):].strip().startswith("user "):
                info["req_users"].append(text)
            if data == "allow":
                if " when " not in text or not text.endswith(":"):
                    errors.append(Diag(ln, "V1", "malformed allow",
                                       "Use `allow <action> when <condition>:` quoting one never invariant."))
                elif not any(len(content_words(text) & content_words(n)) >= 2
                             for n in nevers):
                    errors.append(Diag(ln, "A1", "allow matches no never invariant",
                                       "Quote the invariant it narrows."))
            continue
        if kind == "returnblock":
            returnblock_ind = ind
            continue
        if kind in ("assign", "bareword"):
            in_block = returnblock_ind is not None and ind > returnblock_ind
            if kind == "assign" and not in_block and not follows_run(idx):
                errors.append(Diag(ln, "V1", f"stray assignment {text!r}",
                                   "Assignments live in run args or return: blocks."))
                continue
            if kind == "bareword" and not in_block:
                errors.append(Diag(ln, "V1", f"stray name {text!r}",
                                   "Bare names live in return: blocks only."))
                continue
            if not in_block:
                continue  # run arg; values checked at the run site
            if kind == "assign":
                m = ASSIGN_RE.match(text)
                name, val = m.group(1), m.group(2).strip()
                if name not in produces:
                    errors.append(Diag(ln, "R2", f"return names undeclared produces entry {name!r}",
                                       "Return a skill produces entry."))
                else:
                    info["returned"].add(name)
                if VAR_ONLY.fullmatch(val):
                    note_read(val)
                    check_bound(val, ln, "return value")
            else:
                if text not in produces:
                    errors.append(Diag(ln, "R2", f"return names undeclared produces entry {text!r}",
                                       "Return a skill produces entry."))
                else:
                    info["returned"].add(text)
                note_read(text)
                check_bound(text, ln, "return value")
            continue
        # kind == "action"
        verb, rest = data, text[len(data):].strip()
        if verb == "generate":
            info["has_generate"] = True
            info.setdefault("gen_line", ln)
        tgt = as_target(text)
        if tgt and VAR_ONLY.fullmatch(tgt) and verb not in ("save", "write", "return"):
            bindings.add(tgt)
            info["binds"].setdefault(tgt, ln)
        if verb == "open":
            target = strip_as_clause(rest)
            if not target:
                errors.append(Diag(ln, "E1", "open names no target",
                                   "Name a resource, path, or accepts entry."))
                continue
            name = match_resource(target, resources)
            if target and not name and target not in accepts:
                errors.append(Diag(ln, "E1", f"open target {target!r} matches no resource, path, or accepts entry",
                                   "Declare the resource or fix the name."))
            elif name:
                info["covered_reads"].add(name)
        elif verb == "read":
            src = from_source(text)
            if src is not None:
                if VAR_ONLY.fullmatch(src):
                    note_read(src)
                name = match_resource(src, resources)
                if name:
                    info["covered_reads"].add(name)
                elif src not in accepts and src not in bindings:
                    errors.append(Diag(ln, "E1", f"read source {src!r} matches no resource, path, or accepts entry",
                                       "Declare the resource or fix the name."))
            else:
                target = strip_as_clause(rest)
                if not target:
                    errors.append(Diag(ln, "E1", "read names no target",
                                       "Name a path or use `read X from Y`."))
                    continue
                name = match_resource(target, resources)
                if target and not name and target not in accepts:
                    errors.append(Diag(ln, "E1", f"read target {target!r} matches no resource, path, or accepts entry",
                                       "Declare the resource or fix the name."))
                elif name:
                    info["covered_reads"].add(name)
        elif verb in ("write", "save"):
            if verb == "write":
                m = WITH_RE.search(text)
                target = m.group(1).strip() if m else ""
                val = rest.split(" with ", 1)[0].strip()
            else:
                target = tgt or ""
                val = rest.rsplit(" as ", 1)[0].strip() if " as " in rest else ""
            if VAR_ONLY.fullmatch(val):
                note_read(val)
                check_bound(val, ln, f"{verb} value")
            name = match_resource(target, resources) if target else None
            if not target or (not name and target not in accepts):
                errors.append(Diag(ln, "E1", f"{verb} target {target!r} matches no resource, path, or accepts entry",
                                   "Declare the resource or fix the path."))
            elif name:
                info["covered_writes"].add(name)
                if str(resources[name].get("immutable", "")).lower() == "true":
                    errors.append(Diag(ln, "E3", f"{verb} to immutable resource {name!r}",
                                       "Write elsewhere or drop immutable:."))
        elif verb == "show" or verb == "discard":
            if VAR_ONLY.fullmatch(rest):
                note_read(rest)
                check_bound(rest, ln, f"{verb} value")
        elif verb == "ask":
            info.setdefault("all_asks", []).append(text)
            if not (tgt and VAR_ONLY.fullmatch(tgt)):
                info["asks"].append((ln, text))
        elif verb == "apply":
            m = WITH_RE.search(text)
            target = m.group(1).strip() if m else ""
            if VAR_ONLY.fullmatch(target):
                note_read(target)
                check_bound(target, ln, "apply target")
        elif verb == "run":
            m = re.fullmatch(r"run\s+(\S+)\s+with:", text)
            if not m:
                errors.append(Diag(ln, "V1", f"malformed run {text!r}",
                                   "Use `run <flow> with:` plus indented args."))
                continue
            target = m.group(1)
            if "." in target:
                warnings.append(Diag(ln, "W8", f"cross-skill run {target!r} unchecked",
                                     "Resolved at load; keep accepts aligned."))
            elif target not in flows:
                errors.append(Diag(ln, "R3", f"run target {target!r} is no flow in this file",
                                   "Run a declared flow."))
            else:
                info["edges"].append((ln, target))
            j = idx + 1
            while j < len(stmts) and stmts[j][1] > ind and \
                    classify_flow_line(stmts[j][2])[0] == "assign":
                am = ASSIGN_RE.match(stmts[j][2])
                val = am.group(2).strip()
                if VAR_ONLY.fullmatch(val):
                    note_read(val)
                    if val not in bindings and val not in accepts \
                            and val not in resources:
                        errors.append(Diag(stmts[j][0], "U1", f"run argument value {val!r} is not bound",
                                           "Bind it with `as` or pass an accepts entry."))
                j += 1
            bindings.update(produces)
        elif verb == "return":
            m = re.fullmatch(r"return\s+(\S+)\s+as\s+([A-Za-z_][\w-]*)\s*", text)
            if not m:
                errors.append(Diag(ln, "V1", f"malformed return {text!r}",
                                   "Use `return <binding> as <name>` or a `return:` block."))
                continue
            val, name = m.group(1), m.group(2)
            if VAR_ONLY.fullmatch(val):
                note_read(val)
                check_bound(val, ln, "return value")
            if name not in produces:
                errors.append(Diag(ln, "R2", f"return names undeclared produces entry {name!r}",
                                   "Return a skill produces entry."))
            else:
                info["returned"].add(name)
        elif verb == "abort":
            pass
        # generic from-check for non-read verbs (single-token sources only)
        if verb != "read":
            src = from_source(text)
            if src and VAR_ONLY.fullmatch(src):
                note_read(src)
                check_bound(src, ln, "from source")
    # leading-require run (base-indent requires; labels don't break it)
    leading = []
    if stmts:
        for ln, ind, text in stmts:
            if ind != base_ind:
                continue
            kind, data = classify_flow_line(text)
            if kind == "label":
                continue
            if kind == "gate" and data == "require":
                leading.append(text[len("require"):].strip())
            else:
                break
    info["leading"] = leading
    # return-to targets and end-of-flow shape
    for ln, target in info["returntos"]:
        if target not in info["labels"]:
            errors.append(Diag(ln, "L1", f"return to unknown label {target!r}",
                               "Declare it with `label {target}:`."))
    for ln0, ind0, var in info["foreach"]:
        for ln, ind, text in stmts:
            if ind > ind0 and ln > ln0:
                t = as_target(text)
                if t == var:
                    errors.append(Diag(ln, "L1", f"mutation of for-each variable {var!r}",
                                       "Bind a new name instead."))
    base_stmts = [(ln, t) for ln, ind, t in stmts if ind == base_ind]
    if base_stmts:
        ln, text = base_stmts[-1]
        kind, data = classify_flow_line(text)
        if not (kind == "returnblock" or (kind == "action" and data in ("return", "abort"))):
            errors.append(Diag(ln, "R2", "flow must end in return or abort",
                               "End the flow with a return or abort."))
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
                elif not TYPE_RE.match(str(entry["type"])):
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"{section}.{name} has unknown type {entry['type']!r}",
                                       "Use the closed v0.3 type set."))
        elif section in header:
            errors.append(Diag(find_key_line(fm_lines, section), "F1",
                               f"{section} must be a map",
                               "Use indented name: entries."))
    req = header.get("requires")
    if isinstance(req, dict):
        for flow, conds in req.items():
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
                int(budget.get(sub, "x"))
            except (TypeError, ValueError):
                errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                                   f"budget.{sub} must be an integer",
                                   "Use a token count."))
    elif "budget" in header:
        errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                           "budget must be a map", "Use { header: N, body: M }."))


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
    ctx = {"header": header, "resources": resources, "nevers": nevers,
           "flows": list(logics)}
    infos = {}
    for flow, block in logics.items():
        errs, warns, info = analyze_flow(flow, block["stmts"], ctx)
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
    produces = set((header.get("produces") or {}).keys()) if header else set()
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
            and "appendix" not in appendix_text.lower():
        gen_line = min([i.get("gen_line", 10 ** 9) for i in infos.values()
                        if i["has_generate"]])
        warnings.append(Diag(gen_line if gen_line < 10 ** 9 else 1, "W4",
                             "creative step without appendix guidance",
                             "Add an appendix for generate steps."))
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
        if hcap >= 0 and ht > hcap:
            errors.append(Diag(find_key_line(fm_lines, "budget"), "B1",
                               f"header ~{ht} tokens over budget {hcap} (approx ceil(chars/4))",
                               "Trim prose values."))
        if bcap >= 0 and bt > bcap:
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

