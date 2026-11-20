"""Two-turn live proof: a headless agent with only the skillwren plugin builds a new skill.

Turn 1 should show the requirement inventory, ask for confirmation and write nothing.
Turn 2 (resumed, "confirmed") should draft, check, explain and package the skill.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PLUGIN = r"Z:\SkillWren\plugin"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
CLAUDE = shutil.which("claude")
work = Path(tempfile.mkdtemp(prefix="sw-proj-"))
(work / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n### Added\n\n### Fixed\n", encoding="utf-8")

REQUEST = ("Use skillwren to build a new skill named changelog-entry, in ./changelog-entry. "
           "The skill adds one entry to CHANGELOG.md for a change the user describes. "
           "It must read the current CHANGELOG.md first, ask the user whether the entry belongs "
           "under Added or Fixed when the description does not make that clear, never edit any "
           "file other than CHANGELOG.md, and show the user the new entry before writing it.")


def turn(prompt, resume=None):
    argv = [CLAUDE, "-p", "--output-format", "json", "--model", "sonnet",
            "--plugin-dir", PLUGIN, "--add-dir", PLUGIN, "--setting-sources", "", "--strict-mcp-config",
            "--allowedTools", "Bash(py:*)", "Bash(python3:*)", "Bash(python:*)", "Read", "Write",
            "Edit", "Glob", "Grep", "Skill", "--max-turns", "60"]
    if resume:
        argv += ["--resume", resume]
    proc = subprocess.run(argv, input=prompt, capture_output=True, text=True, cwd=work,
                          encoding="utf-8", timeout=1800)
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        data = {"raw": proc.stdout[-4000:], "stderr": proc.stderr[-2000:]}
    return data


def files():
    return sorted(str(p.relative_to(work)).replace("\\", "/") for p in work.rglob("*") if p.is_file())


first = turn(REQUEST)
after_first = files()
second = turn("Confirmed: the inventory is complete and correct. Go ahead and build it.",
              resume=first.get("session_id"))
after_second = files()
summary = {
    "work": str(work),
    "turn1": {k: first.get(k) for k in ("result", "total_cost_usd", "num_turns", "session_id", "is_error")},
    "files_after_turn1": after_first,
    "turn2": {k: second.get(k) for k in ("result", "total_cost_usd", "num_turns", "is_error")},
    "files_after_turn2": after_second,
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
shutil.copytree(work, OUT / "workdir", dirs_exist_ok=True)
print(json.dumps({"cost": (first.get("total_cost_usd") or 0) + (second.get("total_cost_usd") or 0),
                  "files_after_turn1": after_first, "files_after_turn2": after_second}, indent=1))
