"""Host-load records: which copy of a skill the host actually loaded (SPEC 23).

`ledger check --loaded DIR` only helps when someone names DIR. A Claude Code
`PostToolUse` hook on the `Skill` tool removes that step:

    {"hooks": {"PostToolUse": [{"matcher": "Skill", "hooks": [{"type": "command",
      "command": "skillwren ledger record-load"}]}]}}

The hook input names the skill (`{"skill": "demo"}` or `plugin:skill`) but
not the directory it came from, so this module resolves the name the way
the host does: personal skills (~/.claude/skills) before project skills
(.claude/skills in the working directory or a parent); `plugin:skill`
through `installPath` in ~/.claude/plugins/installed_plugins.json, a
project-scoped install for this directory before a user-scoped one. The
digest is taken at load time, so a later cache update cannot hide what was
loaded. Every candidate is recorded with its digest; when they disagree the
record is marked ambiguous, because the resolution order is the host's and
can change.

`ledger check` without `--loaded` reads `.skillwren/loaded.jsonl` (beside
the ledger directory) and compares the latest load of the run's package,
matched by the `name:` in its SKILL.md, made before the run's last record.
"""
import datetime
import json
import re
import sys
from pathlib import Path

LOADS = "loaded.jsonl"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def skill_name(directory):
    """The `name:` in directory/SKILL.md's frontmatter, or None."""
    path = Path(directory) / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None
    if not text.startswith("---"):
        return None
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"name\s*:\s*(.+?)\s*$", line)
        if match:
            return match.group(1).strip("\"'")
    return None


def _within(child, parent):
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except (ValueError, OSError):
        return False


def candidates(skill, cwd, home):
    """Directories that could hold `skill`, in the host's precedence order."""
    cwd, home = Path(cwd), Path(home)
    found = []
    if ":" in skill:
        plugin, name = skill.split(":", 1)
        registry = home / ".claude" / "plugins" / "installed_plugins.json"
        try:
            plugins = json.loads(registry.read_text(encoding="utf-8")).get("plugins", {})
        except (OSError, ValueError):
            plugins = {}
        entries = [e for key, group in plugins.items() if key.split("@")[0] == plugin
                   for e in group if isinstance(e, dict) and e.get("installPath")]
        project = [e for e in entries if e.get("scope") == "project"
                   and e.get("projectPath") and _within(cwd, e["projectPath"])]
        user = [e for e in entries if e.get("scope") != "project"]
        for entry in project + user:
            found.append(Path(entry["installPath"]) / "skills" / name)
    else:
        found.append(home / ".claude" / "skills" / skill)
        for directory in [cwd, *cwd.parents]:
            found.append(directory / ".claude" / "skills" / skill)
    seen, out = set(), []
    for directory in found:
        key = str(directory.resolve()) if directory.exists() else str(directory)
        if key not in seen and (directory / "SKILL.md").is_file():
            seen.add(key)
            out.append(directory)
    return out


def record_load(event, home=None, out=None, package=None):
    """Append one load record for a PostToolUse(Skill) hook event; returns it,
    or None when the event is not a skill load or nothing resolves.

    `out` is the record file. The default (.skillwren/loaded.jsonl in the
    working directory) is fine for `ledger check`, but the agent can write
    there; a guard skill requirement (SPEC 24) must name a host-owned file
    and the hook must be configured with the same `--out`.

    `package` is the directory the host loaded, when the hook knows it (a
    plugin hook gets it as ${CLAUDE_PLUGIN_ROOT}/<skill>). The record then
    names that copy alone instead of mirroring the host's resolution order."""
    from .ledger import package_identity
    if event.get("tool_name") != "Skill":
        return None
    skill = (event.get("tool_input") or {}).get("skill")
    if not skill:
        return None
    cwd = Path(event.get("cwd") or ".")
    home = Path(home) if home else Path.home()
    found = []
    for directory in ([Path(package)] if package else candidates(skill, cwd, home)):
        try:
            found.append({"path": str(directory),
                          "tree_sha256": package_identity(directory)["tree_sha256"]})
        except Exception:  # an unreadable candidate is not a load
            continue
    if not found:
        return None
    record = {"time": _now(), "skill": skill, "name": skill.split(":")[-1],
              "session": event.get("session_id"), **found[0], "candidates": found,
              "ambiguous": len({c["tree_sha256"] for c in found}) > 1}
    out = Path(out) if out else cwd / ".skillwren" / LOADS
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def latest_load(loads_file, name, before=None):
    """The last load of `name` recorded at or before `before` (ISO time)."""
    try:
        lines = Path(loads_file).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    best = None
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("name") != name:
            continue
        if before is not None and record.get("time", "") > before:
            continue
        best = record
    return best


def hook_main(stream=None, out=None, package=None):
    """Entry point for the hook: never fails the host's tool call."""
    try:
        event = json.loads((stream or sys.stdin).read() or "{}")
        record_load(event, out=out, package=package)
    except Exception as error:  # report, do not block the host
        print(f"skillwren record-load: {error}", file=sys.stderr)
    return 0
