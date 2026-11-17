"""Model adapter for scripts/benchmark_runtime.py, backed by headless Claude Code.

Each invocation reads the trial context on stdin ({prompt, task, tools,
operation, seed, history, max_turns}) and prints {"request": {...},
"tokens": n}: the model's next tool request. No tools, repository, or user
settings are given to the model; it acts only through the returned request.
Environment: SW_RUNTIME_MODEL (default sonnet). Spends provider usage.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

SCHEMA = {"type": "object", "required": ["action"],
          "properties": {"action": {"type": "string", "enum": ["verify", "write", "finish"]},
                         "content": {"type": "string"}}}
SYSTEM = """You are an agent completing a task through a tool interface. Each turn you
issue exactly one request, as JSON:
- {{"action": "verify", "content": "<candidate>"}}: run verification on a candidate
- {{"action": "write", "content": "<candidate>"}}: write the candidate to the target
- {{"action": "finish"}}: stop
Results of your earlier requests are in HISTORY. You have at most {max_turns} turns.

SKILL INSTRUCTIONS:
{prompt}
"""


def main():
    context = json.load(sys.stdin)
    history = [{"request": {k: v for k, v in h["request"].items() if k != "operation"},
                "result": h["result"]} for h in context.get("history", [])]
    user = (f"TASK: {context['task']}\n\nHISTORY ({len(history)} earlier requests):\n"
            + json.dumps(history, indent=1) + "\n\nIssue your next request.")
    model = os.environ.get("SW_RUNTIME_MODEL", "sonnet")
    with tempfile.TemporaryDirectory() as directory:
        prompt_file = Path(directory) / "system.md"
        prompt_file.write_text(SYSTEM.format(max_turns=context.get("max_turns", 6),
                                             prompt=context["prompt"]), encoding="utf-8")
        cmd = [shutil.which("claude") or "claude", "-p", user, "--model", model,
               "--output-format", "json", "--tools", "", "--strict-mcp-config",
               "--no-session-persistence", "--setting-sources", "",
               "--system-prompt-file", str(prompt_file), "--json-schema", json.dumps(SCHEMA)]
        for attempt in range(3):  # transient provider errors: retry, then fail loudly
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=300, cwd=directory)
            if proc.returncode == 0:
                break
            time.sleep(10 * (attempt + 1))
    if proc.returncode != 0:
        print(proc.stderr[-1000:] or proc.stdout[-1000:], file=sys.stderr)
        return 1
    result = json.loads(proc.stdout)
    choice = result.get("structured_output") or json.loads(result["result"])
    usage = result.get("usage") or {}
    tokens = sum(usage.get(k) or 0 for k in ("input_tokens", "output_tokens",
                                             "cache_read_input_tokens",
                                             "cache_creation_input_tokens"))
    if choice.get("action") == "finish":
        request = {"action": "finish"}
    else:
        request = {"action": choice.get("action"), "operation": context["operation"],
                   "content": choice.get("content", "")}
    print(json.dumps({"request": request, "tokens": tokens,
                      "cost_usd": result.get("total_cost_usd")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
