"""Generate the disposable review subject: one reachable injection, one style nit.

Usage: make_subject.py <dest-dir>
"""
import sys
from pathlib import Path

VULNERABLE = '''"""User lookup over shell (change under review)."""
import subprocess
import sys


def find_user(name):
    return subprocess.run("getent passwd " + name, shell=True, capture_output=True, text=True)


def main():
    find_user(sys.argv[1])


if __name__ == "__main__":
    main()
'''

CALLER = '''"""Caller: passes CLI input straight through."""
import sys

from vulnerable import find_user

if __name__ == "__main__":
    find_user(sys.argv[1])
'''

STYLE_NIT = '''"""Helper with an unused variable (style only)."""
_unused_default = 42


def double(value):
    return value * 2
'''


def main():
    dest = Path(sys.argv[1])
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "vulnerable.py").write_text(VULNERABLE, encoding="utf-8")
    (dest / "caller.py").write_text(CALLER, encoding="utf-8")
    (dest / "style_nit.py").write_text(STYLE_NIT, encoding="utf-8")
    (dest / "INSTRUCTIONS.md").write_text(
        "# Subject\n\nReview the change: caller.py now passes CLI input to\n"
        "find_user without validation. Project convention: subprocess calls\n"
        "must use argument lists, never shell=True with interpolation.\n",
        encoding="utf-8")
    print(f"subject in {dest}")


if __name__ == "__main__":
    main()
