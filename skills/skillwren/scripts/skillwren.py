"""SkillWren command line for this skill: no installation, Python 3.9+, standard library only.

Inside an installed plugin the library is bundled beside this script (`../lib`);
in the SkillWren repository checkout it is the repository's `src/`.

Repair budget (0.12.2). When `check` is run on files in a folder named `*-draft` (the
skill's draft folder), this launcher records each check in `<draft>/.skillwren/budget.json`
(digests of the draft's files and of the result; `build` skips `.skillwren/`). A repair is
a check whose draft changed since the previous check. When a check is not clean and either
five repairs have been made or the latest repair left exactly the same result, it prints a
"repair budget spent" line and exits 3, so the stop is a fact the agent reads, not a count
it keeps.
"""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "lib", HERE.parents[2] / "src"):
    if (candidate / "skillwren" / "__init__.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    sys.exit("skillwren: bundled library not found beside this script")

if sys.version_info < (3, 9):
    sys.exit("skillwren: needs Python 3.9 or later")

from skillwren.cli import dispatch  # noqa: E402

REPAIRS = 5
SPENT = 3


def draft_folder(args):
    """The `*-draft` folder holding the checked files, or None."""
    for arg in args:
        path = Path(arg)
        if arg.startswith("-") or not path.is_file():
            continue
        for parent in path.resolve().parents:
            if parent.name.endswith("-draft"):
                return parent
    return None


def digest_tree(folder):
    h = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file() and ".skillwren" not in path.relative_to(folder).parts:
            h.update(path.relative_to(folder).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def budget(folder, result, clean):
    """Record this check; return a reason when the budget is spent, else None."""
    state_file = folder / ".skillwren" / "budget.json"
    try:
        checks = json.loads(state_file.read_text(encoding="utf-8"))["checks"]
    except (OSError, ValueError, KeyError):
        checks = []
    current = {"draft": digest_tree(folder), "result": hashlib.sha256(result.encode()).hexdigest()}
    previous = checks[-1] if checks else None
    checks.append(current)
    state_file.parent.mkdir(exist_ok=True)
    state_file.write_text(json.dumps({"checks": checks}, indent=1), encoding="utf-8")
    repairs = sum(1 for a, b in zip(checks, checks[1:]) if a["draft"] != b["draft"])
    if clean:
        return None
    if previous and previous["draft"] != current["draft"] and previous["result"] == current["result"]:
        return "the last repair left exactly the same problems"
    if repairs >= REPAIRS:
        return f"{repairs} repairs without a clean check"
    return None


def run(argv):
    if not argv or argv[0] != "check":
        return dispatch(["skillwren"] + argv)
    folder = draft_folder(argv[1:])
    if folder is None:
        return dispatch(["skillwren"] + argv)
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            result = dispatch(["skillwren"] + argv)
            code = result if isinstance(result, int) else 0
        except SystemExit as exit_:
            code = exit_.code if isinstance(exit_.code, int) else (0 if exit_.code is None else 1)
    sys.stdout.write(out.getvalue())
    sys.stderr.write(err.getvalue())
    text = out.getvalue() + err.getvalue()
    clean = code == 0 and " warning " not in text
    reason = budget(folder, text, clean)
    if reason:
        print(f"skillwren: repair budget spent ({reason}). Stop editing the draft: take the blocked "
              "exit and report the last result, what each repair tried, and what you need from the user.")
        return SPENT
    return code


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
