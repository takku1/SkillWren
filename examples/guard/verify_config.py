"""Example predicate: sensitive configuration must explicitly disable debug."""
import hashlib
import json
import sys

raw = sys.stdin.buffer.read()
try:
    value = json.loads(raw)
    valid = isinstance(value, dict) and value.get('debug') is False
except (ValueError, UnicodeError):
    valid = False
print(json.dumps({'ok': valid, 'input_sha256': hashlib.sha256(raw).hexdigest()}))
raise SystemExit(0 if valid else 1)
