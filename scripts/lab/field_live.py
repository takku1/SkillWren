"""Tier 3 for the 2026-11-19 field response: real headless agents (paid).

    py -3 scripts/lab/field_live.py OUTDIR [--reps 3] [--model sonnet] [--arms a,b]

Arms (each rep is a fresh disposable git repository):

- author: the agent must compose `flows/build.md` from a design fragment
  that writes a note and an implement fragment whose exclusion rule forbids
  any earlier write (finding 5). Host checks: the composition checks clean,
  still runs both flows, keeps the note write, implement.md is unchanged,
  and whether the agent saw P3.
- run: the agent builds a small change with the `build-notes` skill under
  the ledger, started with `--package` (findings 5 and 6). Host checks: the
  agent's run passes `ledger check --loaded <installed copy>` and fails as
  `package-mismatch` against a stale copy (changed SKILL.md and guard).
- skip-plain / skip-required: the field's constrained-stack prompt
  ("standard library only") with the stack milestone absent or required
  (finding 7). Host checks: did the agent enter the stack fragment, and did
  the ledger ever call a skipped required fragment complete.

Spends provider usage; the agent and host share one OS account (see
scripts/host_demo.py for the isolation caveat).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from skillwren import ledger  # noqa: E402

LIVE = ROOT / "examples" / "field-live"
APP = '''"""Tiny todo CLI."""
import sys

ITEMS = []


def main(argv):
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''
PROMPTS = {
    # {SW} is a vendored copy of SkillWren outside the subject, so agents are
    # not pointed at this repository (run 1 found them reading its docs).
    "author": (
        "In skill/, add skill/flows/build.md: a SkillWren fragment with one logic flow "
        "`build` that runs the design flow (flows/design.md) and the implement flow "
        "(flows/implement.md), so a build both designs (keeping its design note) and "
        "implements. Check it with `py -3 {SW} check --fragment skill/flows/build.md` "
        "and repeat until it prints clean. Do not edit skill/flows/implement.md. "
        "SkillWren syntax is in skill/flows/*.md; mirror it."),
    "run": "Add a --version flag to src/app.py that prints 1.0. Keep a short design note.",
    "skip": ("Make the todo list in src/app.py persist between runs so items survive "
             "restarts. Python standard library only."),
}
REQUIRES = {
    "run": ' --require "exec#guard" --require "write#code"',
    "skip-plain": ' --require "exec#guard" --require "write#code"',
    "skip-required": (' --require "exec#guard" --require "write#code"'
                      ' --require "exec#stack-profiles"'),
}
ARMS = ("author", "run", "skip-plain", "skip-required")


def git(subject, *args):
    subprocess.run(["git", "-C", str(subject), "-c", "user.name=host",
                    "-c", "user.email=host@localhost", *args],
                   check=True, capture_output=True)


def vendor(base):
    """A private SkillWren copy for the agent: src plus the launcher."""
    tool = base / "tool"
    shutil.copytree(ROOT / "src", tool / "src",
                    ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    (tool / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts" / "skillwren.py", tool / "scripts" / "skillwren.py")
    return (tool / "scripts" / "skillwren.py").as_posix()


def make_subject(arm, base, sw):
    subject = base / "subject"
    subject.mkdir()
    git(subject, "init", "-q")
    if arm == "author":
        shutil.copytree(LIVE / "author" / "skill", subject / "skill")
        git(subject, "add", "-A")
        git(subject, "commit", "-qm", "fixture")
        return subject, None
    (subject / "src").mkdir()
    (subject / "src" / "app.py").write_text(APP, encoding="utf-8")
    (subject / "docs").mkdir()
    (subject / "docs" / ".keep").write_text("", encoding="utf-8")
    git(subject, "add", "-A")
    git(subject, "commit", "-qm", "fixture")
    skill = subject / ".claude" / "skills" / "build-notes"
    shutil.copytree(LIVE / "build-notes", skill)
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    (skill / "SKILL.md").write_text(text.replace("{SKILLWREN}", sw)
                                    .replace("{REQUIRES}", REQUIRES[arm]), encoding="utf-8")
    return subject, skill


def run_agent(subject, model, budget, prompt, arm):
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("claude CLI not found on PATH")
    # Windows hosts offer both shells; run 1 allowed only Bash and two agents'
    # `py` checks through PowerShell were denied.
    tools = ["Bash(py:*)", "PowerShell(py:*)", "Read", "Write", "Edit", "Glob", "Grep"]
    if arm != "author":
        tools.append("Skill")
    cmd = [claude, "-p", "--model", model, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
           "--permission-mode", "dontAsk", "--max-budget-usd", str(budget),
           "--allowedTools", *tools]
    started = time.monotonic()
    proc = subprocess.run(cmd, input=prompt, cwd=subject, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=1200)
    events = []
    for line in proc.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    return events, proc.returncode, round(time.monotonic() - started, 1), proc.stderr[-2000:]


def digest(events):
    tools, results, final = [], [], {}
    for event in events:
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            content = []
        for block in content:
            if block.get("type") == "tool_use":
                tools.append({"tool": block["name"], "input": block.get("input", {})})
            if block.get("type") == "tool_result":
                body = block.get("content")
                results.append(body if isinstance(body, str) else json.dumps(body))
        if event.get("type") == "result":
            final = event
    return tools, results, {"cost_usd": final.get("total_cost_usd"),
                            "turns": final.get("num_turns"),
                            "final_text": (final.get("result") or "")[-1500:],
                            "denials": len(final.get("permission_denials") or []),
                            "denied": [json.dumps(d.get("tool_input"))[:200]
                                       for d in final.get("permission_denials") or []][:5]}


def check_author(subject, results, sw):
    flows = subject / "skill" / "flows"
    build = flows / "build.md"
    out = {"build_exists": build.is_file(),
           "saw_p3": any("P3" in r for r in results)}
    proc = subprocess.run([sys.executable, sw, "check", "--fragment", str(build)],
                          capture_output=True, text=True)
    out["host_check"] = proc.stdout.strip().splitlines()[-1:] if proc.stdout else []
    out["clean"] = proc.returncode == 0 and out["build_exists"]
    text = build.read_text(encoding="utf-8") if out["build_exists"] else ""
    every = "".join(p.read_text(encoding="utf-8") for p in sorted(flows.glob("*.md")))
    out["runs_design"] = "run design" in text
    out["runs_implement"] = "run implement" in text or "run implement" in every.replace(text, "")
    out["note_kept"] = "write #notes" in every
    diff = subprocess.run(["git", "-C", str(subject), "diff", "--stat", "HEAD", "--", "skill"],
                          capture_output=True, text=True).stdout
    out["implement_unchanged"] = "implement.md" not in diff
    out["changed"] = diff.strip().splitlines()
    out["build_text"] = text
    out["pass"] = all(out[k] for k in ("clean", "runs_design", "runs_implement",
                                       "note_kept", "implement_unchanged"))
    return out


def check_run(subject, skill, arm, base):
    runs = sorted((subject / ".skillwren" / "ledger").glob("*.jsonl"),
                  key=lambda p: p.stat().st_mtime)
    out = {"ledger_runs": len(runs)}
    if not runs:
        out["pass"] = False
        return out
    path = runs[-1]
    records = ledger.load(path)
    head = records[0]
    steps = [r.get("step") for r in records[1:] if r.get("type") == "step"]
    out["steps"] = steps
    out["package_recorded"] = bool(head.get("package"))
    out["required"] = head.get("required")
    good = ledger.check(path, loaded=skill)
    stale = base / "stale"
    shutil.copytree(skill, stale)
    for name, note in (("SKILL.md", "\n<!-- cached 0.8.0 -->\n"), ("guard.py", "\n# 0.8.0\n")):
        with (stale / name).open("a", encoding="utf-8") as stream:
            stream.write(note)
    bad = ledger.check(path, loaded=stale)
    out["host_verdict"] = {k: good[k] for k in ("ok", "valid", "completeness", "outcome",
                                                "package_consistent")}
    out["exclusion_violations"] = sum(len(r["violations"]) for r in good["exclusions"])
    out["stale_verdict"] = {k: bad[k] for k in ("ok", "outcome", "package_consistent")}
    out["stale_caught"] = bad["package_consistent"] is False and not bad["ok"]
    out["code_changed"] = bool(subprocess.run(
        ["git", "-C", str(subject), "status", "--porcelain", "--", "src"],
        capture_output=True, text=True).stdout.strip())
    out["guard_refusals"] = sum(1 for r in records[1:] if r.get("step") == "exec#guard"
                                and r.get("exit") not in (0, None))
    out["stack_entered"] = "exec#stack-profiles" in steps
    out["skip_reported_complete"] = (arm == "skip-required" and not out["stack_entered"]
                                     and good["completeness"] == "complete")
    out["pass"] = (out["package_recorded"] and good["package_consistent"] is True
                   and out["stale_caught"] and not out["skip_reported_complete"])
    return out


def one(arm, rep, model, budget, keep):
    try:
        return _one(arm, rep, model, budget, keep)
    except Exception as error:  # one failed rep must not lose the others
        return {"arm": arm, "rep": rep, "model": model, "error": repr(error),
                "cost_usd": None, "host": {"pass": False}}


def _one(arm, rep, model, budget, keep):
    with tempfile.TemporaryDirectory(prefix=f"sw-live-{arm}-",
                                     ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        sw = vendor(base)
        subject, skill = make_subject(arm, base, sw)
        prompt = PROMPTS["skip" if arm.startswith("skip") else arm].replace("{SW}", sw)
        events, code, seconds, stderr = run_agent(subject, model, budget, prompt, arm)
        tools, results, meta = digest(events)
        host = (check_author(subject, results, sw) if arm == "author"
                else check_run(subject, skill, arm, base))
        record = {"arm": arm, "rep": rep, "model": model, "exit": code, "seconds": seconds,
                  **meta, "tool_calls": len(tools),
                  "read": sorted({Path(t["input"].get("file_path", "")).name for t in tools
                                  if t["tool"] == "Read"} - {""}),
                  "host": host,
                  "outside_reads": sorted({t["input"].get("file_path", "") for t in tools
                                           if t["tool"] == "Read"
                                           and not str(t["input"].get("file_path", "")).replace("\\", "/")
                                           .lower().startswith(subject.as_posix().lower())})}
        if code != 0:
            record["stderr"] = stderr
        if keep:
            shutil.copytree(subject, keep / f"{arm}-{rep}", ignore=shutil.ignore_patterns(".git"))
        return record


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--budget", type=float, default=1.5)
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--keep", action="store_true", help="copy each subject to OUT/subjects")
    parser.add_argument("--jobs", help="explicit ARM:REP list (rerun interrupted reps);"
                                       " results merge into OUT/results.jsonl by (arm, rep)")
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    keep = out / "subjects" if args.keep else None
    jobs = [(arm, rep) for rep in range(1, args.reps + 1) for arm in args.arms.split(",")]
    if args.jobs:
        jobs = [(job.split(":")[0], int(job.split(":")[1])) for job in args.jobs.split(",")]
    with ThreadPoolExecutor(args.workers) as pool:
        records = list(pool.map(lambda job: one(*job, args.model, args.budget, keep), jobs))
    if args.jobs and (out / "results.jsonl").is_file():
        fresh = {(r["arm"], r["rep"]) for r in records}
        kept = [json.loads(line) for line in
                (out / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        records = [r for r in kept if (r["arm"], r["rep"]) not in fresh] + records
        records.sort(key=lambda r: (r["rep"], ARMS.index(r["arm"])))
    with (out / "results.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")
    summary = {}
    for arm in args.arms.split(","):
        rows = [r for r in records if r["arm"] == arm]
        summary[arm] = {"runs": len(rows), "pass": sum(1 for r in rows if r["host"]["pass"]),
                        "cost_usd": round(sum(r["cost_usd"] or 0 for r in rows), 3)}
        if arm == "author":
            summary[arm]["saw_p3"] = sum(1 for r in rows if r["host"].get("saw_p3"))
        else:
            summary[arm]["stack_entered"] = sum(1 for r in rows if r["host"].get("stack_entered"))
            summary[arm]["stale_caught"] = sum(1 for r in rows if r["host"].get("stale_caught"))
            summary[arm]["exclusion_violations"] = sum(
                r["host"].get("exclusion_violations", 0) for r in rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
