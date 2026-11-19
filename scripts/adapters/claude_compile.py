"""Model adapter for `skillwren compile`, backed by headless Claude Code.

Reads one request on stdin ({"phase": "inventory" | "lower" | "repair" |
"judge", ...}) and prints one JSON reply on stdout. The model gets the
authoring guide, the fragment template, and the inline-form example as its
language reference; no tools, no repository, no user settings. It proposes
only. Spends provider usage.

Environment: SW_COMPILE_MODEL (default sonnet; used for inventory, lower,
repair), SW_JUDGE_MODEL (default opus; a different session, and by default a
different model, from the drafter), SW_ADAPTER_LOG (optional JSONL usage log).
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
JUDGE_CATEGORIES = ['omission', 'invention', 'over_asking', 'permission_expansion', 'permission_restriction', 'control_flow_distortion', 'ordering_distortion']
STRINGS = {"type": "array", "items": {"type": "string"}}
SPAN = {"type": "object", "required": ["file", "lines"],
        "properties": {"file": {"type": "string"},
                       "lines": {"type": "array", "items": {"type": "integer"},
                                 "minItems": 2, "maxItems": 2}}}
KINDS = ["order", "gate", "branch", "decision", "effect", "recovery", "invariant",
         "input", "output", "step-meaning", "context", "unrepresentable"]

SCHEMAS = {
    "inventory": {"type": "object", "required": ["inventory", "questions", "assumptions"],
                  "properties": {
                      "inventory": {"type": "object", "required": ["requirements", "non_requirements"],
                                    "properties": {
                                        "requirements": {"type": "array", "items": {
                                            "type": "object",
                                            "required": ["id", "kind", "text", "evidence", "source"],
                                            "properties": {
                                                "id": {"type": "string"},
                                                "kind": {"type": "string", "enum": KINDS},
                                                "text": {"type": "string"},
                                                "evidence": {"type": "string", "enum": [
                                                    "exec", "user", "effect", "self", "none"]},
                                                "source": {"type": "array", "items": SPAN}}}},
                                        "non_requirements": {"type": "array", "items": {
                                            "type": "object", "required": ["file", "lines", "reason"],
                                            "properties": dict(SPAN["properties"],
                                                               reason={"type": "string"})}}}},
                      "questions": STRINGS, "assumptions": STRINGS}},
    "lower": {"type": "object",
              "required": ["files", "lands", "scaffolding", "questions", "assumptions"],
              "properties": {
                  "files": {"type": "array", "items": {
                      "type": "object", "required": ["path", "content"],
                      "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
                  "lands": {"type": "array", "items": {
                      "type": "object", "required": ["id", "anchors"],
                      "properties": {"id": {"type": "string"}, "anchors": STRINGS}}},
                  "scaffolding": {"type": "array", "items": {
                      "type": "object", "required": ["anchor", "reason"],
                      "properties": {"anchor": {"type": "string"},
                                     "reason": {"type": "string"}}}},
                  "questions": STRINGS, "assumptions": STRINGS}},
    "judge": {"type": "object", "required": JUDGE_CATEGORIES,
              "properties": {key: STRINGS for key in JUDGE_CATEGORIES}},
}
SCHEMAS["repair"] = SCHEMAS["lower"]

INVENTORY_PROMPT = """You are the front end of a compiler from natural-language agent
skills to SkillWren. Your job in this phase is ONLY to list requirements; do
not write any SkillWren yet.

The sources arrive as numbered listings (`  12| text`). Produce an inventory:

- One requirement per obligation, prohibition, check, gate, branch, human
  decision, effect (file written, command run), recovery/repair path,
  ordering ("X before Y", stated or clearly implied), input, output shape,
  step meaning (what a named step must do), or context that changes
  decisions (rubrics, thresholds, examples that decide outcomes).
- `kind` is one of: order, gate, branch, decision, effect, recovery,
  invariant, input, output, step-meaning, context, unrepresentable.
  Use `unrepresentable` for things SkillWren cannot check (taste,
  correlated conditions between branches, optional resources); they will
  be kept as prose and flagged, never dropped.
- `evidence` says what the source demands as proof: `exec` (a command or
  check is run and its result judged), `user` (a person decides or
  confirms), `effect` (an artifact must exist), `self` (the agent's own
  judgment is enough), `none`.
- `source` gives the exact line spans the requirement comes from. A line
  may support several requirements.
- Every nonblank line must be covered: by a requirement, or by a
  `non_requirements` entry with a short reason (heading, rationale that
  changes nothing, an example that decides nothing, boilerplate).
  Prefer a requirement when in doubt; losing a requirement silently is the
  failure this compiler exists to prevent.
- Preserve qualifiers and concrete values (counts, thresholds, names).
  Do not merge distinct requirements into one vague item.
- Put ambiguities in `questions` and anything you had to assume in
  `assumptions`. IDs: R1, R2, ... in source order.
"""

LOWER_PROMPT = """You are the code generator of a compiler from natural-language agent
skills to SkillWren. You receive the numbered sources and a checked
requirement inventory. Write the skill and say where each requirement landed.

Target layout `{layout}`:
- inline: one `SKILL.md` with YAML frontmatter holding only `name` and
  `description` (routing text: what it does, when to use it, what it is not
  for), then the `contract` and `logic` blocks, a `## Step meanings` list
  defining every `apply` step, prose for context/taste/rubrics, and a
  step-to-command table when the source names commands. Follow the INLINE
  EXAMPLE's shape. It is checked with `skillwren check --fragment`.
- fragments: a small `SKILL.md` (name, description, short core, a table
  saying which flow file to read when) plus `flows/<name>.md` files with
  the logic blocks, per the FRAGMENT TEMPLATE.

Rules:
- Every requirement lands somewhere. kinds gate/branch/decision/effect/
  recovery land on a logic statement; kind order lands as an `order:`
  rule using typed IDs (`verify#id before write#id`); invariant lands in
  `always:`/`never:`; input in `inputs:`; output, step-meaning, context and
  unrepresentable land in prose sections (unrepresentable stays prose).
- Evidence: a requirement with evidence `exec` becomes `exec <check> from
  checks as <name>` followed by `verify #id <condition> from <name>`.
  Evidence `user` becomes a decision `ask` plus `require confirmation`.
  Evidence `effect` becomes a `write`/`save`.
- Give every `verify`, `write`, and `exec` that a rule or requirement
  depends on a typed ID; IDs are unique across the skill.
- Every path ends in `return <binding> as <name>`, a `return:` block, or
  `abort with "..."`. A bare `return` is invalid.
- No writes, exec or mutation before a dismissible `ask` (M1); decide first.
- A repair loop re-runs the check and re-verifies before `retry`.
- Abort only where the source says to stop. When the source says to
  record a gap, mark work conditional, report what was not done, or keep
  going with independent work, the `otherwise:` block records it (an
  `apply` or `write` naming the gap) and continues or returns a result
  that states the gap; it does not `abort`. A missing optional reference
  is a gap, not a failure.
- Every `retry` or `return to` loop needs a way out when the source names
  one ("until a blocker prevents progress", "report the blocker"): inside
  the repair, branch on the blocker (`if <failure persists with the same
  evidence>:`) and `return` the recorded blocker and next step, so the
  loop cannot spin forever and the blocker report is reachable.
- A readiness or completeness gate that the source allows to be unmet
  ("identify what is ready versus conditional", "keep unavailable
  prerequisites explicit") is a branch that labels the result, not a gate
  that blocks delivery.
- Only `read` a reference into a binding the flow then uses; otherwise
  describe when to consult it in prose.
- Invent nothing: no steps, permissions, writes, or gates the inventory
  lacks. Do not add `require X exists` gates the source does not ask for;
  declare inputs instead.
- `lands` gives, per requirement ID, the anchors where it landed: a
  literal substring copied exactly from your output (a full statement line
  is best; for an order rule, the rule text), or a line reference `L42`
  (`flows/x.md#L42` in other files) naming one logic statement. Use line
  references for statements whose text repeats (`retry`, `require
  confirmation`, a repeated `exec`).
{reverse}{repair}
=== AUTHORING GUIDE ===
{guide}

=== FRAGMENT TEMPLATE ===
{template}

=== INLINE EXAMPLE ===
{inline}
"""

REVERSE_RULES = """- Reverse traceability is checked: every ask, `require confirmation` or
  `require user`, `abort`, `retry`, `return to`, `write`, `save`, `exec`,
  and `run` must be named by some requirement's anchor, alone (a literal
  that matches several statements justifies none of them). A statement no
  requirement justifies is an invention: an ask is over-asking, a write
  or exec a permission expansion, an abort or retry invented control. The
  fix is to remove it, or to land the requirement that really needs it.
- `scaffolding` lists compiler plumbing the source does not state, each
  {anchor, reason}: only an `exec` that supplies evidence for a verify, or
  a branch, may be scaffolding, and it is reported. Never use it to cover
  an ask, confirmation, abort, retry, write, or run.
- Do not paraphrase the procedure in prose outside the fenced blocks; prose
  is for meanings, context, and commands.
"""

REPAIR_RULES = """
REPAIR PHASE: your previous files and lands are included with the checker's
diagnostics, unbacked verify gates, and inventory findings (I4 no landing,
I5 anchor not found verbatim, I6 wrong placement for the kind, I7 missing
demanded evidence, I9 statement with no source requirement, I12 ask with
no decision behind it, I13 bad scaffolding entry, J1 judge finding with its
failure category). Fix every error without weakening requirements to
silence a rule. Return the full corrected files, lands, and scaffolding.
"""

JUDGE_PROMPT = """You audit a compiled SkillWren skill against its requirement inventory.
You see each requirement and a deterministic plain-language explanation
generated from the compiled skill's syntax tree (not the skill text).
Explanations do not show prose sections, so requirements of kind output,
step-meaning, context, and unrepresentable are out of scope for you unless
the explanation contradicts them.

Classify each problem into exactly one category, as a short phrase that
starts with the requirement ID (or "none:" when no requirement supports
the behaviour):
- omission: a requirement the explanation lacks or weakens (missing gate,
  branch, abort, write, ordering, or evidence).
- invention: behaviour no requirement supports that is not one of the
  categories below (an extra gate, step, retry loop, or abort).
- over_asking: a user question or confirmation where the source sets a
  default, delegates to existing permission, or decides itself.
- permission_expansion: the flow writes, runs, or touches something the
  source does not authorize.
- permission_restriction: the flow adds an approval or blocks an action
  the source already allows (other than by asking: that is over_asking).
- control_flow_distortion: same requirement, different branch structure
  (unconditional made conditional or the reverse, continue made abort,
  a readiness check made a blocking loop).
- ordering_distortion: a required order is reversed, lost, or added.
Wording, IDs, and flow names do not matter unless the meaning changes.
Empty lists are fine when nothing is wrong.
"""


def claude(system, prompt, schema, model):
    # The prompt goes on stdin: full-context sources exceed the Windows 32K
    # command-line limit; the system prompt goes in a file for the same reason.
    cmd = [shutil.which("claude") or "claude", "-p", "--model", model,
           "--output-format", "json", "--tools", "", "--strict-mcp-config",
           "--no-session-persistence", "--setting-sources", "",
           "--json-schema", json.dumps(schema)]
    with tempfile.TemporaryDirectory() as directory:
        prompt_file = Path(directory) / "system.md"
        prompt_file.write_text(system, encoding="utf-8")
        cmd += ["--system-prompt-file", str(prompt_file)]
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=900, cwd=directory)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1000:] or proc.stdout[-1000:])
    result = json.loads(proc.stdout)
    reply = result.get("structured_output") or json.loads(result["result"])
    usage = {"model": model, "cost_usd": result.get("total_cost_usd"),
             "output_tokens": (result.get("usage") or {}).get("output_tokens"),
             "seconds": (result.get("duration_ms") or 0) / 1000}
    return reply, usage


def _sources(request):
    return "\n\n".join(f"=== SOURCE {name} ===\n{text}"
                       for name, text in request["sources"].items())


def build(request):
    phase = request["phase"]
    if phase == "inventory":
        prompt = (f"Entry file: {request['entry']}\n\n{_sources(request)}")
        if request.get("findings"):
            prompt += ("\n\n=== YOUR PREVIOUS INVENTORY ===\n" + json.dumps(request["previous"])
                       + "\n\n=== CHECKER FINDINGS (fix all) ===\n"
                       + json.dumps(request["findings"], indent=1))
        return INVENTORY_PROMPT, prompt
    if phase in ("lower", "repair"):
        system = LOWER_PROMPT.format(
            layout=request["layout"], repair=REPAIR_RULES if phase == "repair" else "",
            reverse=REVERSE_RULES if request.get("reverse", True) else "",
            guide=(ROOT / "docs/current/authoring-guide.md").read_text(encoding="utf-8"),
            template=(ROOT / "docs/current/fragment-template.md").read_text(encoding="utf-8"),
            inline=(ROOT / "examples/host-demo/dep-audit/forms/inline.md").read_text(
                encoding="utf-8"))
        inventory = {"requirements": request["inventory"]["requirements"]}
        prompt = (f"{_sources(request)}\n\n=== INVENTORY ===\n{json.dumps(inventory, indent=1)}")
        if phase == "repair":
            prompt += ("\n\n=== YOUR PREVIOUS FILES ===\n" + json.dumps(request["files"], indent=1)
                       + "\n\n=== YOUR PREVIOUS LANDS ===\n" + json.dumps(request["lands"])
                       + "\n\n=== CHECK DIAGNOSTICS ===\n"
                       + json.dumps(request["diagnostics"], indent=1)
                       + "\n\n=== INVENTORY FINDINGS ===\n"
                       + json.dumps(request["findings"], indent=1)
                       + "\n\n=== UNBACKED VERIFY GATES ===\n"
                       + json.dumps(request["unbacked_verifies"], indent=1))
        return system, prompt
    if phase == "judge":
        requirements = [{k: r[k] for k in ("id", "kind", "text", "evidence") if k in r}
                        for r in request["inventory"]["requirements"]]
        prompt = ("=== REQUIREMENTS ===\n" + json.dumps(requirements, indent=1)
                  + "\n\n" + "\n\n".join(f"=== EXPLANATION {name} ===\n{text}"
                                         for name, text in request["explanations"].items()))
        return JUDGE_PROMPT, prompt
    raise ValueError(f"unknown phase {phase!r}")


def main():
    request = json.load(sys.stdin)
    phase = request["phase"]
    system, prompt = build(request)
    model = (os.environ.get("SW_JUDGE_MODEL", "opus") if phase == "judge"
             else os.environ.get("SW_COMPILE_MODEL", "sonnet"))
    try:
        reply, usage = claude(system, prompt, SCHEMAS[phase], model)
    except (RuntimeError, ValueError, KeyError) as error:
        print(f"claude_compile {phase}: {error}", file=sys.stderr)
        return 1
    if phase in ("lower", "repair"):
        reply["files"] = {item["path"]: item["content"] for item in reply["files"]}
        reply["lands"] = {item["id"]: item["anchors"] for item in reply["lands"]}
    usage["phase"] = phase
    log = os.environ.get("SW_ADAPTER_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(usage) + "\n")
    print(json.dumps(dict(reply, usage=usage)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
