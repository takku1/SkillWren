"""Check a subject repo's manifests against banned deps and licenses.

Reads pyproject.toml/requirements.txt under the subject directory given
as argv[1]. Prints a JSON verdict; exit 0 only when nothing banned and
every license is allowlisted. Evidence-grade: the ledger records the
command, and the guard verifier re-checks the candidate bytes.
"""
import json
import re
import sys
from pathlib import Path

BANNED = {"requests==1.0.0", "urllib3==0.9"}
ALLOWED_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause", "PSF-2.0"}


def main():
    subject = Path(sys.argv[1])
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
    licenses = re.findall(r"license\s*=\s*[\"']([^\"']+)", text, re.IGNORECASE)
    for entry in licenses:
        findings["licenses"][entry] = entry in ALLOWED_LICENSES
    verdict = not findings["banned"] and all(findings["licenses"].values())
    findings["verdict"] = "clean" if verdict else "blocked"
    print(json.dumps(findings, indent=2))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
