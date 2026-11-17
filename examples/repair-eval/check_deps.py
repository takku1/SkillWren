"""Check a repository's manifests against banned deps and licenses.

Usage: check_deps.py <repo> [--out <file>]
Reads pyproject.toml/requirements.txt under <repo>, prints a JSON verdict
and, with --out, writes the same bytes to <file> (the guard candidate).
Exit 0 only when nothing banned and every license is allowlisted.
"""
import json
import re
import sys
from pathlib import Path

BANNED = {"requests==1.0.0", "urllib3==0.9"}
ALLOWED_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause", "PSF-2.0"}


def main(argv):
    out = None
    if "--out" in argv:
        index = argv.index("--out")
        out = Path(argv[index + 1])
        argv = argv[:index] + argv[index + 2:]
    subject = Path(argv[0])
    findings = {"banned": [], "licenses": {}}
    text = ""
    for name in ("pyproject.toml", "requirements.txt"):
        candidate = subject / name
        if candidate.is_file():
            text += candidate.read_text(encoding="utf-8") + "\n"
    for line in text.splitlines():
        match = re.match(r"\s*([A-Za-z0-9_.-]+)==([^\s;,]+)", line)
        if match and f"{match.group(1)}=={match.group(2)}" in BANNED:
            findings["banned"].append(f"{match.group(1)}=={match.group(2)}")
    for entry in re.findall(r"license\s*=\s*\{?\s*(?:text\s*=\s*)?[\"']([^\"']+)",
                            text, re.IGNORECASE):
        findings["licenses"][entry] = entry in ALLOWED_LICENSES
    clean = not findings["banned"] and all(findings["licenses"].values())
    findings["verdict"] = "clean" if clean else "blocked"
    rendered = json.dumps(findings, sort_keys=True)
    print(rendered)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(rendered.encode("utf-8"))
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
