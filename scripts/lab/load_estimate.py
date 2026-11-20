"""Estimate context loaded per task for a skill layout (paid, small).

    py -3 scripts/lab/load_estimate.py TASKS.json SKILL_DIR [SKILL_DIR...] [--model haiku]

For each skill directory (SKILL.md plus on-demand Markdown files) and each
task, a routing probe (a model that sees only the entry SKILL.md, the task,
and the list of other files) names the files it would open; `run <flow>
from <file>` calls in opened files are then followed deterministically.
Tokens are exact cl100k_base counts. Reports total artifact, entry, and
per-task loaded tokens. This estimates host routing; it does not observe an
agent doing the task. Excludes `audit/`.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
RUN_FROM = re.compile(r"^\s*run\s+\S+\s+from\s+(\S+)", re.M)
SCHEMA = {"type": "object", "required": ["open"],
          "properties": {"open": {"type": "array", "items": {"type": "string"}}}}
PROMPT = """You are an agent host. A skill was activated for the task below. You
have read its entry file SKILL.md (shown). Which of the other files would you
open to do this task, following the entry file's own instructions about when
to read what? List only paths from the list; an empty list is fine.

TASK: {task}

OTHER FILES:
{files}

=== SKILL.md ===
{entry}
"""


def tokens(text):
    return len(ENC.encode(text))


def markdown(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*.md")) if "audit" not in p.relative_to(root).parts}


def route(task, files, model):
    others = [name for name in files if name != "SKILL.md"]
    if not others:
        return [], 0
    prompt = PROMPT.format(task=task, files="\n".join(others), entry=files["SKILL.md"])
    cmd = [shutil.which("claude") or "claude", "-p", "--model", model, "--output-format", "json",
           "--tools", "", "--strict-mcp-config", "--no-session-persistence",
           "--setting-sources", "", "--json-schema", json.dumps(SCHEMA)]
    with tempfile.TemporaryDirectory() as directory:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300, cwd=directory)
    result = json.loads(proc.stdout)
    chosen = (result.get("structured_output") or json.loads(result["result"]))["open"]
    return [name for name in chosen if name in files], result.get("total_cost_usd") or 0


def closure(opened, files):
    seen, todo = set(opened), list(opened)
    while todo:
        name = todo.pop()
        base = Path(name).parent
        for target in RUN_FROM.findall(files[name]):
            for candidate in ((base / target).as_posix(), target):
                if candidate in files and candidate not in seen:
                    seen.add(candidate)
                    todo.append(candidate)
    return sorted(seen)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks")
    parser.add_argument("skills", nargs="+")
    parser.add_argument("--model", default="haiku")
    args = parser.parse_args()
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    report, cost = {}, 0.0
    for skill in args.skills:
        files = markdown(skill)
        sizes = {name: tokens(text) for name, text in files.items()}
        per_task = {}
        for task in tasks:
            routed, spent = route(task["task"], files, args.model) if len(files) > 1 else ([], 0)
            cost += spent
            loaded = closure(["SKILL.md"] + routed, files)
            per_task[task["id"]] = {"files": loaded, "tokens": sum(sizes[n] for n in loaded)}
        report[skill] = {"total_tokens": sum(sizes.values()), "entry_tokens": sizes["SKILL.md"],
                         "files": len(files), "tasks": per_task}
    print(json.dumps({"method": "model-routed estimate (entry file + file list + task), "
                                "run-from closure; cl100k_base", "router": args.model,
                      "cost_usd": round(cost, 4), "skills": report}, indent=2))


if __name__ == "__main__":
    main()
