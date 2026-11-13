"""Guard verifier for the audit report: only a clean verdict passes.

A blocked candidate is well-formed but must never become the protected
report, so verification rejects it: without a passing verification
there is no approval to spend, and the write is impossible, not merely
forbidden by prose.
"""
import hashlib
import json
import sys

raw = sys.stdin.buffer.read()
try:
    value = json.loads(raw)
    valid = isinstance(value, dict) and value.get("verdict") == "clean"
except (ValueError, UnicodeError):
    valid = False
print(json.dumps({"ok": valid, "input_sha256": hashlib.sha256(raw).hexdigest()}))
raise SystemExit(0 if valid else 1)
