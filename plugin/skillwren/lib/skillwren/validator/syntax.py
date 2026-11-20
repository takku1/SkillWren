"""Lexical helpers and the SkillWren Frontmatter Profile reader.

Everything here is pure text handling with no rule knowledge: the
diagnostic record, the closed vocabulary, the indented-map parser used for
headers, type and version grammars, and path/resource matching.
"""
import re
from collections import namedtuple

Diag = namedtuple("Diag", ["line", "rule", "msg", "fix"])

FORMAT_VERSION = (0, 6)  # format version; patch releases (0.6.1) share it

STOPWORDS = {"a", "an", "the", "to", "of", "and", "or", "for", "with",
             "on", "in", "please"}
ACTIONS = {"open", "read", "write", "save", "show", "ask", "generate",
           "apply", "run", "return", "abort", "discard", "exec"}
BRANCH = {"if", "unless", "when"}
GATES = {"require", "verify", "allow"}
REQUIRED_KEYS = {"skill", "description", "version", "accepts",
                 "produces", "owns-when", "requires", "flows", "authority",
                 "effects", "risk", "cost", "budget"}
KNOWN_KEYS = REQUIRED_KEYS | {"name", "purpose", "release"}  # purpose defaults to description
BASE_TYPES = {"Text", "Number", "Boolean", "Path", "Artifact", "Theme",
              "ThemeSpec", "Any"}
ACCESS_VALUES = {"read", "create", "read+create", "read+write"}
RESOURCE_KEYS = {"path", "access", "immutable", "glob"}  # glob: 0.5, for conform
VAR_ONLY = re.compile(r"[A-Za-z_][\w-]*\Z")
INTERP_RE = re.compile(r"\{([^{}]+)\}")
AS_RE = re.compile(r"\bas\s+(\S+)\s*$")
FROM_RE = re.compile(r"\bfrom\s+(.+?)(?:\s+as\s+\S+)?\s*$")
WITH_RE = re.compile(r"\bwith\s+(.+?)(?:\s+as\s+\S+)?\s*$")
ASSIGN_RE = re.compile(r"^([A-Za-z_][\w-]*)\s*=\s*(\S.*)$")
# `run <flow> with:` (same file or skill.flow) or, from 0.6,
# `run <flow> from <relative path> with:` (another file's logic block).
RUN_RE = re.compile(r"run\s+(\S+)(?:\s+from\s+(\S+))?\s+with:")
STRICT_OPEN_RE = re.compile(r"^```(logic|contract)\s*$")
HEADER_MAX = 400     # declared header ceiling; Section 10
BODY_DEFAULT = 2500  # declared per skill; above this warns (W11)
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
            if k.strip() in obj:
                return None, i  # Ambiguous declarations must not silently win.
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


def yaml_unsafe_values(raw):
    """Unquoted inline-collection members holding [ ] { }: valid in the profile's
    old reading but rejected by YAML parsers, so hosts drop the whole header."""
    if ":" not in raw:
        return []
    value = raw.split(":", 1)[1].strip()
    if value[:1] in "\"'" or value[:1] not in "[{":
        return []
    inner = value[1:-1] if value[-1:] in "]}" else value[1:]
    bad = []
    for part in split_top_commas(inner):
        member = part.split(":", 1)[1] if value[0] == "{" and ":" in part else part
        member = member.strip()
        if member and member[0] not in "\"'" and any(c in member for c in "[]{}"):
            bad.append(member)
    return bad


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
    """Closed type grammar: base | List<T> | Enum[a, b, ...]."""
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
    """Returns (major, minor) for `X.Y[.Z]`, else None.

    The patch is ignored: patch versions carry no format change, so
    0.4.1 is format-equivalent to 0.4 and validates normally."""
    if not isinstance(s, str):
        return None
    m = VERSION_RE.match(s.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


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


def run_target(text):
    """(flow, path or None) for a well-formed run header, else None."""
    m = RUN_RE.fullmatch(text)
    return (m.group(1), m.group(2)) if m else None
