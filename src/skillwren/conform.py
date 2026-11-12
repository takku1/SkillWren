"""Runtime conformance: run a skill headless and compare what changed with what it declared.

    skillwren conform <skill.md> --prompt TEXT --model MODEL --budget-usd N
                      [--workspace DIR] [--auth-from-profile] [--record DIR]

The skill's folder is installed into a throwaway git workspace (a copy of
--workspace, or empty) at .claude/skills/<skill>. One headless Claude Code
session runs with a fresh CLAUDE_CONFIG_DIR. This does not isolate project
configuration or provide an OS sandbox. Afterwards every changed file must match the
`glob:` of a resource the header lists under effects.creates or mutates;
anything else is an undeclared mutation. An `ask` cannot reach a user in a
headless run, so it counts as a dismissal (SPEC section 12): if the session
tried to ask, it must have changed nothing. Shell commands the session ran
are listed; running any (other than read-only git status/diff) while the
header declares no `effects.executes` counts as an undeclared command.

--record DIR appends one JSON line per run to DIR/conform-runs.jsonl,
including failed and errored runs, so later sessions can see which runs
were observed and how they ended without trusting anyone's memory.

This spends model usage. It is never part of `skillwren check` or CI.
Exit codes: 0 conforms, 1 violations, 2 usage or environment error.
"""
import argparse
import datetime
import fnmatch
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .validator import (match_resource, parse_block, parse_contract, parse_fences,
                        split_frontmatter, validate_file)

LOGIN = Path.home() / ".claude" / ".credentials.json"
# Interpreters differ by host: on Windows `python` and `python3` can be
# Microsoft Store stubs and only the `py` launcher works, so allow all three.
TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Skill", "Bash(python:*)", "Bash(python3:*)",
         "Bash(py:*)", "Bash(git status:*)", "Bash(git diff:*)"]
READ_ONLY_COMMANDS = ("git status", "git diff")
RECORD_FILE = "conform-runs.jsonl"


def declared_globs(skill_path):
    """Globs of resources the header says the skill may create or mutate."""
    text = Path(skill_path).read_text(encoding="utf-8-sig")
    fm_lines, body_lines, body_first = split_frontmatter(text)
    header, _ = parse_block(list(fm_lines or []), 0, 0)
    header = header if isinstance(header, dict) else {}
    _logics, _order, contract, _appendix, _diags = parse_fences(body_lines, body_first)
    resources, _always, _nevers = parse_contract(contract, [])
    effects = header.get("effects") if isinstance(header.get("effects"), dict) else {}
    globs, missing = [], []
    for entry in (effects.get("creates") or []) + (effects.get("mutates") or []):
        name = match_resource(entry, resources)
        glob = (resources.get(name) or {}).get("glob") if name else None
        if glob:
            globs.append(str(glob).strip().strip("\"'"))
        else:
            missing.append(entry)
    return header.get("skill", Path(skill_path).parent.name), globs, missing


def undeclared(changed, globs):
    return [p for p in changed if not any(fnmatch.fnmatchcase(p, g) for g in globs)]


def declares_executes(skill_path):
    """True when the header lists at least one effects.executes entry."""
    text = Path(skill_path).read_text(encoding="utf-8-sig")
    fm_lines, _body, _first = split_frontmatter(text)
    header, _ = parse_block(list(fm_lines or []), 0, 0)
    effects = header.get("effects") if isinstance(header, dict) else None
    executes = effects.get("executes") if isinstance(effects, dict) else None
    return bool(executes) and isinstance(executes, list)


def commands_from(events):
    """Shell commands the session asked to run, in order."""
    commands = []
    for event in events:
        message = event.get("message")
        if event.get("type") != "assistant" or not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if (isinstance(item, dict) and item.get("type") == "tool_use"
                    and item.get("name") in ("Bash", "PowerShell")):
                command = (item.get("input") or {}).get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def undeclared_commands(commands, executes_declared):
    if executes_declared:
        return []
    # A deliberately small exact-token language, not a shell parser. Unknown
    # options, paths, quoting and shell operators receive no exemption.
    allowed = {
        "status": {"--short", "--porcelain", "--branch", "-s", "-b"},
        "diff": {"--stat", "--name-only", "--name-status", "--cached", "--staged"},
    }
    def exempt(command):
        if any(c in command for c in "\r\n\x00"):
            return False
        words = command.split()
        return (len(words) >= 2 and words[0] == "git"
                and words[1] in allowed
                and all(w in allowed[words[1]] for w in words[2:]))
    return [c for c in commands if not exempt(c)]


def skill_digest(skill_path):
    """sha256 over the skill folder's files, so a record pins what ran."""
    root = Path(skill_path).parent
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def append_record(directory, entry):
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    with (target / RECORD_FILE).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, sort_keys=True) + "\n")


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def snapshot(work):
    """Observe final file contents independently of Git's mutable index/ignores.

    Do not follow symlinks. This is a before/after observer, not a sandbox
    or an audit of transient writes, network effects, or paths outside work.
    """
    files = {}
    def fail(error):
        raise error

    for directory, dirs, names in os.walk(work, followlinks=False,
                                          onerror=fail):
        dirs[:] = [name for name in dirs if name != ".git"]
        for name in list(dirs) + names:
            path = Path(directory) / name
            if name == ".git":
                continue
            relative = path.relative_to(work).as_posix()
            if path.is_symlink():
                files[relative] = ("link", os.readlink(path))
            elif path.is_file():
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                files[relative] = ("file", path.stat().st_mode, digest.hexdigest())
    return files


def run_session(skill_path, args):
    errors, _ = validate_file(skill_path)
    if errors:
        raise ValueError("invalid skill: " + "; ".join(d.msg for d in errors))
    skill_id, globs, missing = declared_globs(skill_path)
    base = Path(tempfile.mkdtemp(prefix="skillwren-conform-"))
    work, config = base / "work", base / "config"
    try:
        if args.workspace:
            # Never import Git metadata (including worktree pointers/hooks).
            shutil.copytree(args.workspace, work, symlinks=True,
                            ignore=shutil.ignore_patterns(".git"))
        else:
            work.mkdir()
        shutil.copytree(Path(skill_path).parent, work / ".claude" / "skills" / skill_id,
                        symlinks=True, ignore=shutil.ignore_patterns(".git"))
        for step in (["init", "-q"], ["config", "user.email", "conform@example.invalid"],
                     ["config", "user.name", "conform"], ["config", "core.autocrlf", "false"],
                     ["add", "-A"], ["commit", "-qm", "workspace", "--allow-empty"]):
            git(work, *step)
        config.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "ANTHROPIC"))}
        if args.auth_from_profile:
            shutil.copy2(LOGIN, config / ".credentials.json")
        elif os.environ.get("ANTHROPIC_API_KEY"):
            env["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
        else:
            raise ValueError("Pass --auth-from-profile or set ANTHROPIC_API_KEY.")
        env["CLAUDE_CONFIG_DIR"] = str(config)
        before = snapshot(work)
        proc = subprocess.run(
            [getattr(args, "claude", None) or "claude", "-p", f"/{skill_id} {args.prompt}", "--output-format", "stream-json", "--verbose",
             "--model", args.model, "--max-budget-usd", str(args.budget_usd),
             "--permission-mode", "acceptEdits", "--allowedTools", *TOOLS],
            cwd=work, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=args.timeout)
        events = []
        for line in proc.stdout.splitlines():
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    events.append(event)
            except json.JSONDecodeError:
                pass
        result = next((e for e in reversed(events) if e.get("type") == "result"), {})
        if proc.returncode:
            raise ValueError(f"Claude session failed (exit {proc.returncode}).")
        if not result:
            raise ValueError("Claude session returned no result event.")
        if result.get("subtype") != "success" or result.get("is_error"):
            raise ValueError(f"Claude session failed ({result.get('subtype', 'unknown')}).")
        commands = commands_from(events)
        asks = 0
        for event in events:
            message = event.get("message")
            if event.get("type") != "assistant" or not isinstance(message, dict):
                continue
            content = message.get("content")
            if not isinstance(content, list):
                continue
            asks += sum(isinstance(c, dict) and c.get("type") == "tool_use"
                        and c.get("name") == "AskUserQuestion" for c in content)
        after = snapshot(work)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return {
        "skill": skill_id, "declared_globs": globs, "effects_without_glob": missing,
        "changed": changed, "undeclared": undeclared(changed, globs),
        "asks": asks, "dismissal_violation": bool(asks and changed),
        "commands": commands,
        "undeclared_commands": undeclared_commands(commands, declares_executes(skill_path)),
        "cost_usd": result.get("total_cost_usd"), "status": result.get("subtype"),
        "result": (result.get("result") or "")[:2000],
    }


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren conform", description="Run a skill headless and check its changes against its declared effects.")
    parser.add_argument("skill")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--budget-usd", type=float, required=True)
    parser.add_argument("--workspace")
    parser.add_argument("--auth-from-profile", action="store_true")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    parser.add_argument("--record", metavar="DIR",
                        help=f"append one JSON line per run to DIR/{RECORD_FILE}")
    args = parser.parse_args(argv)
    if not math.isfinite(args.budget_usd) or args.budget_usd <= 0:
        parser.error("--budget-usd must be finite and positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    # Launch the resolved path: npm installs a claude.cmd shim that a bare
    # name cannot start on Windows without a shell.
    args.claude = shutil.which("claude")
    if args.claude is None:
        print("skillwren conform: claude CLI not found on PATH.", file=sys.stderr)
        return 2
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    record = {"started": started, "skill": str(args.skill), "prompt": args.prompt,
              "model": args.model, "budget_usd": args.budget_usd}
    try:
        record["skill_sha256"] = skill_digest(args.skill)
        report = run_session(args.skill, args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"skillwren conform: {error}", file=sys.stderr)
        if args.record:
            _record(args.record, dict(record, outcome="error", error=str(error)))
        return 2
    ok = not report["undeclared"] and not report["dismissal_violation"]
    ok = ok and not report.get("undeclared_commands")
    report["conforms"] = ok
    if args.record:
        _record(args.record, dict(record, outcome="conforms" if ok else "violations",
                                  report=report))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"skill {report['skill']}: {len(report['changed'])} changed, cost {report['cost_usd']}")
        for entry in report["effects_without_glob"]:
            print(f"  note: effects entry {entry!r} has no resource glob; its changes count as undeclared")
        for p in report["undeclared"]:
            print(f"  undeclared mutation: {p}")
        for command in report.get("undeclared_commands", []):
            print(f"  undeclared command: {command}")
        if report["dismissal_violation"]:
            print(f"  dismissal violation: the session asked {report['asks']} question(s) and still changed files")
        print("conforms" if ok else "does not conform")
    return 0 if ok else 1


def _record(directory, entry):
    try:
        append_record(directory, entry)
    except OSError as error:
        print(f"skillwren conform: could not write record: {error}", file=sys.stderr)
