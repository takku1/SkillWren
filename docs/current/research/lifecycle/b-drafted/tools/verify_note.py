"""Guard verifier for the coverage note: only a verdict field passes.

A gaps verdict is well-formed but must never become the protected note
without human triage, so verification rejects it: the note can only be
written for a clean check in this workflow.
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
