# Model A/B/C evaluation plan (pending provider + budget)

Status: scripted arms done, model arms not run. No model results are
claimed here.

## What the scripted run shows

90 paired trials (5 scenarios x 3 arms x 6 repetitions, seeds paired
across arms), raw traces in `runtime-ab-comparison.jsonl`, aggregates in
`runtime-ab-summary.json`:

- Arms A/B: 30/30 tasks complete, 24 unauthorized writes each, 0 false
  blocks. A and B behave identically because the scripted adversary
  ignores the prompt; only a model adapter can separate them.
- Arm C: 12/30 complete (attack scenarios are blocked by design), 0
  unauthorized writes, 0 false blocks.

This measures enforcement mechanics, not whether structured prompts
improve model behavior.

## Model protocol (to run)

Same model, tools, context, and budgets across arms; at least 30 paired
trials per arm across multiple tasks; record task completion,
unauthorized effects, false denials, latency, and tokens; report rates
with 95% confidence intervals.

```text
py -3 scripts/benchmark_runtime.py --output docs/current/research/runtime-model.jsonl \
  --summary docs/current/research/runtime-model-summary.json \
  --repetitions 30 --adapter '["python", "adapter.py"]'
```

The adapter is a trusted program: each invocation reads the task context
as JSON on stdin and writes `{"request": {...}, "tokens": n}` on stdout
(see `scripts/benchmark_runtime.py` for the schema). Sandbox it if it
runs untrusted code. Every adapter invocation spends provider usage.

Predeclared bar for beta: guarded arm cuts unauthorized effects versus
the unguarded arms with no rise in false denials, at 30+ paired trials
per arm. The A/B-vs-C gap isolates enforcement, not SkillWren syntax
over equivalent prose; a syntax claim needs a prose arm held to equal
content.
