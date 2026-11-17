"""Model adapter for `skillwren draft`, backed by headless Claude Code.

Reads {"intent": text} on stdin, prints {"flow", "assumptions", "questions",
"usage"} on stdout. The model sees the authoring guide and fragment template
as its language reference, no tools, no repository, no user settings. It
proposes only; `draft` never approves. Spends provider usage.

Environment: SW_DRAFT_MODEL (default sonnet), SW_ADAPTER_LOG (optional
JSONL file that receives one usage record per call).
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = {"type": "object", "required": ["flow", "assumptions", "questions"],
          "properties": {"flow": {"type": "string"},
                         "assumptions": {"type": "array", "items": {"type": "string"}},
                         "questions": {"type": "array", "items": {"type": "string"}}}}
INSTRUCTIONS = """You draft SkillWren workflow fragments from natural-language intent.
Output a single Markdown fragment file in the `flow` field: an optional title,
an optional `contract` block with `order:` rules, and one `logic` block per
flow. Follow the authoring guide and fragment template below exactly; the
result must pass `skillwren check --fragment`.

Rules:
- Encode every requirement the intent states: each check, gate, branch,
  human decision, abort, retry/repair loop, write, and ordering constraint.
- Invent nothing the intent does not say: no extra steps, permissions,
  writes, asks, or constraints. Put anything you had to assume in
  `assumptions` and anything ambiguous in `questions`.
- When the intent names flows (for example `f06:`), use those exact flow
  names, one flow each. Otherwise name the single flow after its purpose.
- Use typed IDs (`verify #id ...`, `write #id ...`, `ask #id ...`) for steps
  that an `order:` rule references, and reference them as `verify#id`.
  IDs must be unique across the whole fragment.
- Never paraphrase the procedure outside the fenced blocks.
{extra}
=== AUTHORING GUIDE ===
{guide}

=== FRAGMENT TEMPLATE ===
{template}
"""

# Prompt 2 (0.10) targets the defect classes the 0.9 fidelity run found:
# gates that lost their evidence, untyped guard verbs, bare returns, and
# invented existence gates.
PROMPT_V2_RULES = """- Every check the intent mentions is an observation: run it with
  `exec <check> from checks as <name>` and judge it with
  `verify #id <condition> from <name>`. A verify without `from` is your own
  judgment and loses the evidence; use one only when the intent gives no
  check to run, and say so in `assumptions`.
- Give every `verify` and `write` a typed ID, even when no order rule names
  it, so a guard can bind it.
- Every path ends in `return <binding> as <name>`, a `return:` block, or
  `abort`; a bare `return` is invalid.
- Do not add `require <input> exists` gates the intent does not ask for.
  Declare inputs in the contract (`inputs:`) instead.
- A repair loop re-checks before `retry`: exec the check again and verify
  its new result inside the repair block.
"""


def main():
    request = json.load(sys.stdin)
    intent = request["intent"]
    version = os.environ.get("SW_DRAFT_PROMPT", "2")
    system = INSTRUCTIONS.format(
        extra=PROMPT_V2_RULES if version == "2" else "",
        guide=(ROOT / "docs/current/authoring-guide.md").read_text(encoding="utf-8"),
        template=(ROOT / "docs/current/fragment-template.md").read_text(encoding="utf-8"))
    model = os.environ.get("SW_DRAFT_MODEL", "sonnet")
    cmd = [shutil.which("claude") or "claude", "-p", "Intent:\n\n" + intent,
           "--model", model, "--output-format", "json", "--tools", "",
           "--strict-mcp-config", "--no-session-persistence", "--setting-sources", "",
           "--json-schema", json.dumps(SCHEMA)]
    with tempfile.TemporaryDirectory() as directory:
        prompt_file = Path(directory) / "system.md"
        prompt_file.write_text(system, encoding="utf-8")
        cmd += ["--system-prompt-file", str(prompt_file)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=600, cwd=directory)
    if proc.returncode != 0:
        print(proc.stderr[-1000:] or proc.stdout[-1000:], file=sys.stderr)
        return 1
    result = json.loads(proc.stdout)
    proposal = result.get("structured_output") or json.loads(result["result"])
    usage = {"model": model, "cost_usd": result.get("total_cost_usd"),
             "output_tokens": (result.get("usage") or {}).get("output_tokens"),
             "seconds": (result.get("duration_ms") or 0) / 1000}
    log = os.environ.get("SW_ADAPTER_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(usage) + "\n")
    print(json.dumps(dict(proposal, usage=usage)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
