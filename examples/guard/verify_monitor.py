"""Example predicate: runtime monitor passes; echoes the input digest."""
import hashlib
import json
import sys

raw = sys.stdin.buffer.read()
print(json.dumps({'ok': True, 'input_sha256': hashlib.sha256(raw).hexdigest()}))
