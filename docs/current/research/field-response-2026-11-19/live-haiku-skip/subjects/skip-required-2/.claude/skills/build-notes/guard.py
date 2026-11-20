"""Run guard (live-test stand-in): refuses to start over unseen code edits.

Exit 1 when files under src/ differ from git HEAD, like full-stack's guard
refusing uncommitted edits it did not see. Design notes in docs/ are fine.
"""
import subprocess
import sys

changed = subprocess.run(["git", "status", "--porcelain", "--", "src"],
                         capture_output=True, text=True).stdout.strip()
if changed:
    print("guard: refusing to start; unseen code edits:\n" + changed)
    sys.exit(1)
print("guard: started")
