# NL compiler: first runs (2026-11-18)

`skillwren compile` (design: `../../design/nl-compiler.md`) on two real
full-context sources, Sonnet 5.5 for inventory/lower/repair, Opus 5.5 as
judge in separate sessions. One run per arm: read the direction, not the
exact size. Judge verdicts are model review, not ground truth.

## full-stack 0.2.0 prose (`full-stack-0.2/`)

Source: the 48-line entry plus six references (32,566 bytes), frozen in
`full-stack-0.2/FROZEN.md`. Run 1 used the first lowering prompt; run 2
added rules against invented aborts, exitless retry loops, blocking
readiness gates, and unused reference reads.

| Measure | Run 1 | Run 2 |
|---|---|---|
| Valid after repair (bound 3) | yes, 2 repair rounds | yes, 2 repair rounds + 1 judge repair |
| Inventory first try | coverage complete | coverage complete |
| Requirements / non-requirements | 87 / 43 | 90 / 46 |
| Every requirement landed (I4-I7) | yes | yes |
| Generated `review.json` validates | yes | yes |
| Unbacked verifies | 0 | 0 |
| Check warnings | 22 (W5, W9, W15) | 33 (W5 15, W9 13, W15 5) |
| Judge dropped / added / changed (published bytes) | 3 / 4 / 3 | 0 / 3 / 4 |
| `abort` statements | 7 | 1 |
| Output bytes (inline, always loaded) | 28,032 | 32,190 |
| Cost | $1.75 (incl. re-judge) | $1.92 |

Run 1 was compiled before the compiler re-judged after a judge-driven
repair, so its manifest verdict (6 / 2 / 5) is for an earlier draft;
`runs/run1-rejudge.json` is the verdict on the published bytes. The fix
(judge again after the judge repair) is in `nlcompile.py` and tested.

What the judge still finds is a pattern, not noise: **over-asking**. The
compiled flows ask the user where the source says to default (design-only
unless asked to build) or to follow already-applicable permissions. It
appears in both runs and in the dogfood run. The remaining items are
local (a roadmap write without checking for an existing one; a failed
check reported as "absent evidence").

**Size.** The inventory makes the compiler keep everything, and the inline
layout puts it all in the always-loaded file: about 5x the prose entry
(5,778 bytes, references on demand) and about 3x the hand conversion
(9,858 bytes). Faithful, but expensive per activation. Runs 3 and 4
below measure the fragments layout against it.

## Layout comparison: runs 3 and 4 (2026-11-20)

Same source and prompts as run 2, current compiler (reverse traceability
enforced, re-judge after a judge repair). Run 3 `--layout fragments`, run 4
`--layout inline`. Runner: `scripts/lab/compile_runs.sh`. The first
attempts on 2026-11-18 failed early (adapter failure in `lower`; a Windows
process-start failure, exit 0xC0000142, with the two arms in parallel); a
first rerun of run 4 on 2026-11-20 died silently when the account usage
limit was reached. Their logs are in `runs/failed-2026-11-18/` and
`runs/failed-2026-11-20/`. The counted runs went one arm at a time.

| Measure | Run 3 fragments | Run 4 inline |
|---|---|---|
| Valid after repair (bound 3) | yes | yes |
| Requirements / non-requirements | 90 / 43 | 93 / 45 |
| Unbacked verifies | 0 | 0 |
| Judge findings left (published bytes) | 1 ordering distortion (research synthesis before gathering, R77/R80) | 1 over-asking (asks plan-or-build where the source defaults to planning, R3) |
| Output bytes | 954 entry + 31,025 in 3 flows | 23,867, always loaded |
| Cost | $2.52 | $2.30 |

Neither run is approved: each leaves one judge finding for review, which
is the compiler's intended stop.

**Load per task** (`load-layouts.json`; `scripts/lab/load_estimate.py`,
Haiku router over `tasks.json`, cl100k tokens, $0.01). The estimator
follows every `run ... from` statically, so for fragments it counts the
research and implement flows on every task even though the design flow
calls them only on some branches; the branch-following figure counts
them only for the tasks that need them.

| Skill | Total | Entry | Mean loaded per task |
|---|---|---|---|
| Prose source (references on demand) | 5,632 | 1,005 | 3,299 |
| Hand conversion (`reference/full-stack-logic.md`) | 1,983 | 1,983 | 1,983 |
| Run 4 inline | 4,365 | 4,365 | 4,365 |
| Run 3 fragments, static closure | 5,700 | 192 | 5,700 |
| Run 3 fragments, branch-following | 5,700 | 192 | 4,264 |

Fragments barely help on this source: the design flow is read on every
request and holds 3,713 of the 5,700 tokens, so splitting off research
and implement saves about 100 tokens per task against inline. Both
compiled forms load more per task than the prose source and about twice
the hand conversion. What would help is splitting the design flow itself
(registry, existing-project and terminology handling are conditional in
the source) or a lowering rule that keeps conditional guidance in
on-demand references, as the prose does. The load figures are
model-routed estimates, not observed agent reads.

## Dogfood: SkillWren's own conversion skill (`dogfood-skillwren/`)

Source: `skills/skillwren/SKILL.md` as of this session (a copy is in
`source/`). Valid after one repair; 34 requirements; judge found 1 dropped
and 1 added on the published bytes; $0.80. The run used the run-2 prompt:
every repair loop got a blocker exit, a missing reference records a gap.

Both judge findings are real and both trace to the source:

- dropped: "strictly smaller before publication" softened into "record a
  tradeoff". The source said both things; the model silently chose one.
  The source skill is now fixed to say what the tool does (an optimized
  build publishes only a smaller candidate; otherwise package plainly and
  report the tradeoff).
- added: a user confirmation around paid evaluations the source does not
  require (the over-asking pattern again).

Compiling the skill also surfaced a stale claim in it ("flow-file sets are
not built yet"), now corrected.

## What this shows and does not show

Shows: on two real prose sources the pipeline reaches a valid skill within
the repair bound, accounts for every source line, lands every requirement
where its kind requires, and turns the residual semantic risk into a
short, requirement-referenced list. Run 2's prompt rules removed the
invented aborts and exitless loops the first run had.

Does not show: that the output is equivalent to the source, that it is
better than the hand conversion, or that an agent follows it better. No
human has reviewed these outputs. One run per arm.

## Open

- Over-asking: a lowering rule (or an inventory field for "who decides by
  default") is the obvious next step; tune it on a second source, not on
  this benchmark alone, to avoid overfitting one skill.
- Bounded retry: the language has no bounded-retry construct; runs encode
  "stop at a blocker" as a branch inside each repair. A construct would be
  a SPEC change (owner decision).
- Fragment layout is measured (runs 3 and 4): it does not cut load on
  this source because the always-read design flow dominates. Next: split
  conditional design guidance out of the entry flow, then re-measure.
- Human review of at least one compiled output.
