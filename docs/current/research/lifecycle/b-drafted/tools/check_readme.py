"""List CLI commands from --help and compare against README mentions.

Subject layout: <subject>/tool.py (argparse CLI) and <subject>/README.md.
Prints {"undocumented": [...], "verdict": "clean"|"gaps"}; exit 0 only on
clean. The guard verifier re-checks the verdict byte.
"""
import json
import re
import subprocess
import sys
from pathlib import Path


def main():
    subject = Path(sys.argv[1])
    proc = subprocess.run([sys.executable, str(subject / "tool.py"), "--help"],
                          capture_output=True, text=True)
    commands = re.findall(r"^\s{2,}(\w[\w-]*)", proc.stdout, re.MULTILINE)
    readme = (subject / "README.md").read_text(encoding="utf-8")
    missing = [c for c in dict.fromkeys(commands) if c not in readme]
    verdict = "clean" if not missing else "gaps"
    print(json.dumps({"undocumented": missing, "verdict": verdict}, indent=2))
    return 0 if verdict == "clean" else 1


if __name__ == "__main__":
    sys.exit(main())
