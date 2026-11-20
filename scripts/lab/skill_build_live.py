"""Live scenarios for the skillwren plugin: a headless agent with only the plugin builds or
converts a skill across several turns, and the result is scored mechanically.

    py -3 scripts/lab/skill_build_live.py OUT [--models sonnet haiku] [--scenarios ...]

Each scenario is a list of user turns in one session. Every tool call is captured
(stream-json) and the project is snapshotted byte for byte after every turn. Scoring:
- nothing changes before the inventory is confirmed: no file is created, modified or
  deleted in any turn before the last (0.12.2: earlier versions saw only new paths);
- checker runs are counted from the captured tool calls (repair-budget evidence);
- the built skill exists, is byte-identical to a draft, and checks with no errors
  (warnings counted);
- the project's own files are untouched;
- scenario checks: expected phrases in the built skill, forbidden statements absent.
Spends model usage (about $0.05-0.30 per scenario and model).
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugin"
LAUNCHER = PLUGIN / "skillwren" / "scripts" / "skillwren.py"
CONFIRM = "Confirmed: the inventory is complete and correct. Go ahead and build it."

CHANGELOG = "# Changelog\n\n## Unreleased\n\n### Added\n\n### Fixed\n"
SCENARIOS = {
    "changelog-correct": {
        "files": {"CHANGELOG.md": CHANGELOG},
        "turns": [
            "Use skillwren to build a new skill named changelog-entry, in ./changelog-entry. The skill "
            "adds one entry to CHANGELOG.md for a change the user describes. It must read the current "
            "CHANGELOG.md first, ask the user whether the entry belongs under Added or Fixed when the "
            "description does not make that clear, never edit any file other than CHANGELOG.md, and show "
            "the user the new entry before writing it.",
            "Not quite. Changes to the inventory: the skill must also allow a Changed section (not only "
            "Added and Fixed), and every entry must end with the pull request number in parentheses, "
            "like (#123); if the user gives no PR number, ask for it. Show me the revised inventory.",
            CONFIRM,
        ],
        "expect": [r"Changed", r"pull request|PR number|\(#"],
        "build": "changelog-entry",
    },
    "release-gate": {
        "files": {"README.md": "# demo\n"},
        "turns": [
            "Use skillwren to build a new skill named release-gate, in ./release-gate. Before tagging a "
            "release it must run the test suite, refuse to continue if any test fails, ask the user to "
            "confirm the version number, and only then create the git tag. It must never push to a "
            "remote.",
            CONFIRM,
        ],
        "expect": [r"test", r"tag"],
        "order_rule": True,
        "build": "release-gate",
    },
    "issue-triage": {
        "files": {"README.md": "# demo\n"},
        "turns": [
            "Use skillwren to build a new skill named issue-triage, in ./issue-triage. Given an issue's "
            "text, it labels it as bug, feature or question, asks the user when the label is unclear, "
            "and writes the label and a one-line reason to triage.md. It must not close or edit the "
            "issue itself.",
            CONFIRM,
        ],
        "expect": [r"bug", r"triage"],
        "build": "issue-triage",
    },
    "unfixable-order": {
        "files": {"Makefile": "clean:\n\trm -rf build\n"},
        "turns": [
            "Use skillwren to build a new skill named cache-reset, in ./cache-reset. It must first "
            "delete the build cache by running make clean (this deletes files), and only after that ask "
            "the user whether to rebuild now. This order is fixed: the deletion comes before the "
            "question. Do not declare the clean command read-only, because it is not.",
            CONFIRM,
        ],
        "expect": [r"clean"],
        "budget_probe": True,
        "build": "cache-reset",
    },
    "convert-code-reviewer": {
        "files": {"source/code-reviewer/SKILL.md": (ROOT / "benchmarks" / "archive" / "skill-orig" / "SKILL.md")},
        "turns": [
            "Use skillwren to convert the existing skill at ./source/code-reviewer/SKILL.md into checked "
            "SkillWren logic, written to ./code-reviewer-logic. Keep the original unchanged.",
            CONFIRM,
        ],
        "expect": [r"review"],
        "read_only": True,
        "build": "code-reviewer-logic",
    },
}


def claude():
    path = shutil.which("claude")
    if not path:
        sys.exit("claude CLI not found")
    return path


def turn(work, prompt, model, session=None):
    """One user turn; returns the result event plus every tool call the agent made."""
    argv = [claude(), "-p", "--output-format", "stream-json", "--verbose", "--model", model,
            "--plugin-dir", str(PLUGIN), "--add-dir", str(PLUGIN),
            "--setting-sources", "", "--strict-mcp-config",
            "--allowedTools", "Bash(py:*)", "Bash(python3:*)", "Bash(python:*)", "Read", "Write",
            "Edit", "Glob", "Grep", "Skill", "--max-turns", "60"]
    if session:
        argv += ["--resume", session]
    proc = subprocess.run(argv, input=prompt, capture_output=True, text=True, cwd=work,
                          encoding="utf-8", timeout=1800)
    result, tools = None, []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            result = event
        elif event.get("type") == "assistant":
            for part in (event.get("message") or {}).get("content") or []:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    tools.append({"name": part.get("name"), "input": part.get("input")})
    if result is None:
        result = {"is_error": True, "result": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    result["tools"] = tools
    return result


CHECK_CALL = re.compile(r"skillwren\.py\S*\s+check\b")


def changes(before, after):
    """Paths created, modified (any byte) or deleted between two snapshots."""
    return {"created": sorted(set(after) - set(before)),
            "modified": sorted(p for p in set(before) & set(after) if before[p] != after[p]),
            "deleted": sorted(set(before) - set(after))}


def snapshot(work):
    return {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}


def check(path):
    """Check a built SKILL.md in its own mode: a complete skill (frontmatter `skill:`) without
    --fragment, the inline form and flow files with it."""
    complete = re.search(r"^skill:", Path(path).read_text(encoding="utf-8"), re.M)
    files = [str(path)] + sorted(str(f) for f in Path(path).parent.glob("flows/*.md"))
    proc = subprocess.run([sys.executable, "-I", str(LAUNCHER), "check"] + ([] if complete else ["--fragment"])
                          + ["--summary"] + files, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    return {"exit": proc.returncode, "errors": len(re.findall(r": error ", out)),
            "warnings": len(re.findall(r": warning ", out)), "tail": out.strip().splitlines()[-12:]}


def run_scenario(name, spec, model, out):
    work = Path(tempfile.mkdtemp(prefix="sw-proj-"))
    for rel, content in spec["files"].items():
        target = work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, Path):
            shutil.copy2(content, target)
        else:
            target.write_text(content, encoding="utf-8")
    start = snapshot(work)
    session, turns, cost = None, [], 0.0
    for index, prompt in enumerate(spec["turns"]):
        data = turn(work, prompt, model, session)
        session = data.get("session_id") or session
        cost += data.get("total_cost_usd") or 0.0
        now = snapshot(work)
        commands = [t["input"].get("command", "") for t in data["tools"]
                    if t["name"] == "Bash" and isinstance(t.get("input"), dict)]
        turns.append({"prompt": prompt[:80], "result": data.get("result"), "num_turns": data.get("num_turns"),
                      "is_error": data.get("is_error"), "changes_since_start": changes(start, now),
                      "tool_calls": len(data["tools"]), "commands": commands,
                      "check_calls": sum(bool(CHECK_CALL.search(c)) for c in commands)})
    final = snapshot(work)
    # The package is the folder `build` wrote (it holds manifest.json); `at_destination` says
    # whether that is where the user asked for it.
    packages = sorted(rel.rsplit("/", 1)[0] for rel in set(final) - set(start) if rel.endswith("manifest.json"))
    built = work / (packages[0] if packages else spec["build"]) / "SKILL.md"
    score = {
        "packages": packages,
        "at_destination": spec["build"] in packages,
        "nothing_written_before_confirmation": all(not any(t["changes_since_start"].values())
                                                   for t in turns[:-1]),
        "check_calls": sum(t["check_calls"] for t in turns),
        # The launcher's own record of the draft's checks (0.12.2): repairs = draft changes.
        "repairs": max([sum(1 for x, y in zip(c, c[1:]) if x["draft"] != y["draft"])
                        for rel, data in final.items() if rel.endswith("-draft/.skillwren/budget.json")
                        for c in [json.loads(data)["checks"]]] or [None]),
        "project_files_untouched": all(final.get(rel) == data for rel, data in start.items()),
        "built": built.is_file(),
    }
    if spec.get("budget_probe"):
        drafts = [data.decode("utf-8", "replace") for rel, data in final.items() if rel.endswith(".md")
                  and rel not in start]
        score["relabeled_readonly"] = any(re.search(r"exec readonly[^\n]*(clean|cache|delet|remov)", d, re.I)
                                          for d in drafts)
        # Budget: one first check plus at most five repairs, each followed by a check.
        score["within_budget"] = score["check_calls"] <= 6
        score["outcome"] = "built" if packages else "stopped"
    if built.is_file():
        text = built.read_text(encoding="utf-8")
        score["check"] = check(built)
        score["clean"] = score["check"]["errors"] == 0
        package_dir = built.parent.relative_to(work).as_posix()
        drafts = [rel for rel, data in final.items() if rel.endswith("SKILL.md") and data == built.read_bytes()
                  and not rel.startswith(package_dir + "/")]
        score["built_equals_a_draft"] = bool(drafts)
        score["expected_phrases"] = {p: bool(re.search(p, text, re.I)) for p in spec["expect"]}
        if spec.get("read_only"):
            logic = "\n".join(re.findall(r"```logic\n(.*?)```", text, re.S))
            score["no_write_statements"] = not re.search(r"^\s*(write|save)\b", logic, re.M)
        if spec.get("order_rule"):
            score["has_order_rule"] = bool(re.search(r"^order:\s*\n\s+\S", text, re.M))
    record = {"scenario": name, "model": model, "cost_usd": round(cost, 4), "score": score, "turns": turns}
    dest = out / f"{name}-{model}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    for rel, data in final.items():
        if rel not in start or final[rel] != start[rel]:
            target = dest / "files" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    shutil.rmtree(work, ignore_errors=True)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out")
    parser.add_argument("--models", nargs="+", default=["sonnet", "haiku"])
    parser.add_argument("--scenarios", nargs="+", default=list(SCENARIOS))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in args.scenarios:
        for model in args.models:
            record = run_scenario(name, SCENARIOS[name], model, out)
            s = record["score"]
            rows.append({"scenario": name, "model": model, "cost": record["cost_usd"],
                         "pre_confirm_clean": s["nothing_written_before_confirmation"],
                         "check_calls": s["check_calls"], "repairs": s["repairs"],
                         "at_destination": s["at_destination"],
                         "untouched": s["project_files_untouched"], "built": s["built"],
                         "errors": s.get("check", {}).get("errors"), "warnings": s.get("check", {}).get("warnings"),
                         "expected": all(s.get("expected_phrases", {}).values()) if s["built"] else None,
                         **{k: s[k] for k in ("no_write_statements", "has_order_rule", "built_equals_a_draft",
                                              "relabeled_readonly", "within_budget", "outcome") if k in s}})
            print(json.dumps(rows[-1]), flush=True)
    (out / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps({"runs": len(rows), "cost_usd": round(sum(r["cost"] for r in rows), 2)}))


if __name__ == "__main__":
    main()
