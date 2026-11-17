"""Claude Code PreToolUse hook (arm H): an ordinary host-enforcement baseline.

Blocks Write/Edit of REPORT.md unless the written content equals a fresh
dependency check of the current repository and that check is clean.
Edits of REPORT.md are always blocked (the report must be written whole).
Exit 2 blocks the tool call and shows stderr to the agent.
"""
import json
from pathlib import Path
import subprocess
import sys

CHECK = Path(__file__).resolve().parent / "check_deps.py"

event = json.load(sys.stdin)
tool_input = event.get("tool_input") or {}
path = str(tool_input.get("file_path", ""))
if Path(path).name != "REPORT.md":
    sys.exit(0)
if event.get("tool_name") != "Write":
    print("REPORT.md must be written whole with Write, not edited.", file=sys.stderr)
    sys.exit(2)
repo = Path(event.get("cwd") or ".")
fresh = subprocess.run([sys.executable, "-I", str(CHECK), str(repo)],
                       capture_output=True, text=True)
expected = fresh.stdout.strip()
content = str(tool_input.get("content", "")).strip()
if fresh.returncode != 0:
    print("Blocked: the dependency check of the current repository is not clean.",
          file=sys.stderr)
    sys.exit(2)
if content != expected:
    print("Blocked: REPORT.md must contain exactly the current check's findings.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)
