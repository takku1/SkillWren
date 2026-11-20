"""The typed-reference grammar, defined once (SPEC 21, field report 2026-11-19).

A statement carries an operation ID as `<verb> #<id> ...`; an order rule or
a ledger step names it as `<verb>#<id>`. IDs are lowercase letters, digits
and hyphens, starting with a letter. Every consumer (P2, order matching, the
ledger, the workflow renderer, return parsing) uses these patterns, so a
static check and a runtime matcher cannot disagree on what an ID is.
tests/test_refs.py runs each consumer against one table.
"""
import re

ID = r"[a-z][a-z0-9-]*"
VERB = r"[a-z]+"

REFERENCE_RE = re.compile(rf"({VERB})#({ID})")
STATEMENT_ID_RE = re.compile(rf"({VERB})\s+#({ID})(?=[\s:]|$)")
TYPED_RETURN_BLOCK_RE = re.compile(rf"return\s+#({ID}):")
RETURN_RE = re.compile(rf"return\s+(?:#{ID}\s+)?(\S+)\s+as\s+([A-Za-z_][\w-]*)\s*")


def reference(text):
    """(verb, id) when text is exactly a typed reference such as `verify#deps`."""
    m = REFERENCE_RE.fullmatch(text.strip())
    return m.groups() if m else None


def statement_id(text):
    """(verb, id) when a statement starts `<verb> #<id>`, else None."""
    m = STATEMENT_ID_RE.match(text.strip())
    return m.groups() if m else None
