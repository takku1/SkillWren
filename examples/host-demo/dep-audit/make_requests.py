"""Build guard request lines (verify, then write) from a candidate file.

Usage: make_requests.py <candidate.json> <requests.jsonl>
The candidate bytes are carried unchanged; the guard binds approval to
exactly these bytes.
"""
import json
import sys
from pathlib import Path

content = Path(sys.argv[1]).read_bytes().decode("utf-8")
lines = [{"action": "verify", "operation": "write#report", "content": content},
         {"action": "write", "operation": "write#report", "content": content}]
out = Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
print(f"wrote 2 requests ({len(content)}-byte candidate) to {out}")
