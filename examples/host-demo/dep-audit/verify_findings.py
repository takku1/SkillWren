"""verify #deps: exit 0 only when the candidate findings are clean.

Usage: verify_findings.py <candidate.json>
Run through `ledger exec --step "verify#deps"` so the gate is recorded
as evidence with its exit code, not as a self-reported note.
"""
import json
import sys
from pathlib import Path

try:
    findings = json.loads(Path(sys.argv[1]).read_bytes())
    clean = findings.get("verdict") == "clean" and not findings.get("banned")
except (OSError, ValueError, AttributeError):
    clean = False
print("clean" if clean else "blocked")
sys.exit(0 if clean else 1)
