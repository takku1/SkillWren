"""Document layout: fences, the contract block, and the appendix.

Two layouts share one reader:

- **skill** (default): strict body order, exactly one contract block with
  resources/always/never, no prose between semantic blocks (SPEC 10).
- **fragment** (0.6): a Markdown file that embeds `logic` blocks among
  prose, as on-demand flow files do. Other code fences are opaque examples,
  prose may sit anywhere, and the contract block is optional (SPEC 20).
"""
import re
from collections import namedtuple

from .syntax import (ACCESS_VALUES, RESOURCE_KEYS, STRICT_OPEN_RE, VAR_ONLY,
                     Diag, has_tab_indent, is_kebab, strip_quotes)

Contract = namedtuple("Contract", ["resources", "always", "nevers", "order", "inputs"])
OrderRule = namedtuple("OrderRule", ["line", "first", "then", "text"])

SECTION_ORDER = ("resources", "always", "never", "inputs", "order")
SKILL_SECTIONS = {"resources", "always", "never", "order"}
FRAGMENT_SECTIONS = {"always", "never", "inputs", "order"}
REQUIRED_SKILL_SECTIONS = ("resources", "always", "never")
CONTEXT_RE = re.compile(r"(`{4,})context ([a-z][a-z0-9]*(?:-[a-z0-9]+)*) (instruction|example|data)")


def _scan_blocks(body_lines, first_lineno, fragment, diags):
    """Find semantic blocks. Returns (blocks, context_starts, foreign)."""
    blocks = []  # (kind, open_lineno, open_idx, content, close_idx)
    context_starts, foreign = [], set()
    i, n = 0, len(body_lines)
    while i < n:
        raw = body_lines[i]
        lineno = first_lineno + i
        opaque = CONTEXT_RE.fullmatch(raw)
        if opaque:
            context_starts.append(i)
            delimiter = opaque.group(1)
            i += 1
            while i < n and body_lines[i] != delimiter:
                i += 1
            if i == n:
                diags.append(Diag(lineno, "F2", "unclosed context block",
                                  "Close the context with its exact opening fence width."))
            i += 1
            continue
        m = STRICT_OPEN_RE.match(raw)
        if m:
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
            blocks.append((m.group(1), lineno, open_idx, content, i))
            i += 1
            continue
        stripped = raw.strip()
        if stripped.startswith("```") or (fragment and stripped.startswith("~~~")):
            if fragment:
                # Opaque example: skip to its matching close, any language.
                fence = stripped[:len(stripped) - len(stripped.lstrip(stripped[0]))]
                start = i
                i += 1
                while i < n and not body_lines[i].strip().startswith(fence):
                    i += 1
                foreign.update(range(start, min(i, n - 1) + 1))
                i += 1
                continue
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
    return blocks, context_starts, foreign


def _read_logic(blocks, diags):
    logics, order, contract = {}, [], None
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
    return logics, order, contract


def _covered(blocks):
    covered = set()
    for _, _, open_idx, content, close_idx in blocks:
        covered.add(open_idx)
        covered.add(close_idx)
        for k in range(len(content)):
            covered.add(open_idx + 1 + k)
    return covered


def parse_fences(body_lines, first_lineno, fragment=False):
    """Returns (logics, order, contract, appendix_text, diags).

    Skill layout: semantic fences are exactly ```logic / ```contract; the
    contract block precedes all logic blocks; no prose may sit between
    semantic blocks and no semantic block may follow appendix content.
    Lines before the first fence are an ignored preamble (titles).

    Fragment layout: only the contract-before-logic rule remains; every
    line outside semantic blocks is guidance text (the appendix).
    """
    diags = []
    n = len(body_lines)
    blocks, context_starts, foreign = _scan_blocks(body_lines, first_lineno, fragment, diags)
    logics, order, contract = _read_logic(blocks, diags)

    def contract_first():
        contract_idx = next((b[2] for b in blocks if b[0] == "contract"), None)
        if contract_idx is not None:
            for info, lineno, open_idx, _, _ in blocks:
                if info == "logic" and open_idx < contract_idx:
                    diags.append(Diag(lineno, "F2",
                                      "contract block must precede logic blocks",
                                      "Move the contract block first."))

    if fragment:
        contract_first()
        covered = _covered(blocks)
        appendix_text = "\n".join(line for j, line in enumerate(body_lines)
                                  if j not in covered)
        return logics, order, contract, appendix_text, diags
    if blocks:
        covered = _covered(blocks)
        first_open = min(b[2] for b in blocks)
        last_close = max(b[4] for b in blocks)
        for start in context_starts:
            if start < last_close:
                diags.append(Diag(first_lineno + start, "F2",
                                  "context blocks must follow all semantic blocks",
                                  "Move context into the appendix after the final logic block."))
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
        contract_first()
        last_end = last_close + 1
    else:
        last_end = 0
    appendix_text = "\n".join(body_lines[last_end:])
    # Diagnostics keep the historical order: fence scan, flow headers, layout,
    # then contract position. Callers sort stably by line, so order matters.
    return logics, order, contract, appendix_text, diags


def _read_order(entries, diags):
    rules = []
    for ln, _ind, text in entries:
        body = text[2:].strip() if text.startswith("- ") else text
        parts = re.split(r"\s+before\s+", body)
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            diags.append(Diag(ln, "F2", f"malformed order entry {body!r}",
                              "Use `<earlier statement> before <later statement>`,"
                              " with `before` exactly once."))
            continue
        rules.append(OrderRule(ln, parts[0].strip(), parts[1].strip(), body))
    return rules


def _read_inputs(entries, diags):
    names = {}
    for ln, _ind, text in entries:
        body = text[2:].strip() if text.startswith("- ") else text
        for name in re.split(r"[,\s]+", body.strip()):
            if not name:
                continue
            if not VAR_ONLY.fullmatch(name):
                diags.append(Diag(ln, "F2", f"input {name!r} is not a binding name",
                                  "List bare binding names, for example `request, design`."))
            else:
                names.setdefault(name, ln)
    return names


def read_contract(contract, diags, fragment=False):
    """Parse the contract block into a Contract. Appends F2 diags."""
    resources, always, nevers = {}, [], []
    if contract is None:
        if not fragment:
            diags.append(Diag(1, "F2", "missing contract block",
                              "Add one fenced contract block with resources/always/never."))
        return Contract(resources, always, nevers, [], None)
    allowed = FRAGMENT_SECTIONS if fragment else SKILL_SECTIONS
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
        if ind == 0 and text.endswith(":") and text[:-1] in allowed:
            current = text[:-1]
            if current in sections:
                diags.append(Diag(ln, "F2", f"duplicate {text} section",
                                  "Keep one of each."))
            sections[current] = (ln, [])
        elif ind == 0:
            names = "/".join(s + ":" for s in SECTION_ORDER if s in allowed)
            diags.append(Diag(ln, "F2", f"unexpected {text!r} in contract block",
                              f"Only {names} live here."))
        elif current is None:
            diags.append(Diag(ln, "F2", "contract line outside any section",
                              "Place it under resources:/always:/never:."))
        else:
            sections[current][1].append((ln, ind, text))
    if not fragment:
        for need in REQUIRED_SKILL_SECTIONS:
            if need not in sections:
                diags.append(Diag(contract["line"], "F2",
                                  f"contract block missing {need}: section",
                                  f"Add the {need}: section."))
    check_order = fragment or all(s in sections for s in REQUIRED_SKILL_SECTIONS)
    if check_order:
        lines = [sections[s][0] for s in SECTION_ORDER if s in sections]
        if lines != sorted(lines):
            diags.append(Diag(contract["line"], "F2",
                              "contract sections out of order",
                              "Use " + ", ".join(s + ":" for s in SECTION_ORDER if s in allowed)
                              + " in that order."))
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
                                  f" read, create, read+create, read+write, got {res['access']!r}",
                                  "Use the canonical access value."))
            if "immutable" in res and res["immutable"] not in ("true", "false"):
                diags.append(Diag(res["line"], "F2",
                                  f"resource {name!r} immutable must be true or false",
                                  "Use `true` or `false`."))
    if "always" in sections:
        always = [t for _, _, t in sections["always"][1]]
    if "never" in sections:
        nevers = [t for _, _, t in sections["never"][1]]
    order = _read_order(sections["order"][1], diags) if "order" in sections else []
    inputs = _read_inputs(sections["inputs"][1], diags) if "inputs" in sections else None
    return Contract(resources, always, nevers, order, inputs)


def parse_contract(contract, diags):
    """Skill-layout contract as (resources, always, nevers). Appends F2 diags."""
    parsed = read_contract(contract, diags)
    return parsed.resources, parsed.always, parsed.nevers
