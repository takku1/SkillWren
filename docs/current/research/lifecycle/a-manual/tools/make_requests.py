"""Build guard request lines from a candidate file byte-for-byte.

Usage: make_requests.py <candidate.json> <out.jsonl> [operation]
Writes a raw write (must be denied), then verify, then write.
"""
import json
import sys
from pathlib import Path

operation = sys.argv[3] if len(sys.argv) > 3 else "write#report"
candidate = Path(sys.argv[1]).read_bytes().decode("utf-8-sig")
content = json.dumps(json.loads(candidate))
lines = [
    {"action": "write", "operation": operation, "content": content},
    {"action": "verify", "operation": operation, "content": content},
    {"action": "write", "operation": operation, "content": content},
]
Path(sys.argv[2]).write_text(
    "".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
print(f"wrote 3 requests with {len(content)}-byte candidate")
