"""Mint the Skill B guard policy with pinned digests."""
import hashlib
import json
import sys
from pathlib import Path

target = Path(sys.argv[1]).resolve()
policy_path = Path(sys.argv[2])
verifier = str(Path(__file__).resolve().parent / "verify_note.py")
python = str(Path(sys.executable).resolve())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


policy = {"version": 1, "operations": {"write#note": {
    "target": str(target), "argv": [python, "-I", verifier],
    "pins": {python: digest(python), verifier: digest(verifier)},
    "timeout": 5}}}
policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
print(f"policy for {target} -> {policy_path}")
