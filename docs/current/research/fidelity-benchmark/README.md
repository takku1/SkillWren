# Semantic fidelity benchmark

Does a skill built by SkillWren mean what its source meant? A valid SkillWren
program can be a wrong translation, and a right translation can still be
disobeyed, so three scores are kept apart and never combined:

1. **Preservation**: every obligation, prohibition, exception, ordering,
   authority boundary and output rule of the source is in the built skill
   at the same strength (`preserved`, `weakened`, `missing`).
2. **Introduction**: what the built skill adds that the source never stated
   or authorized, and whether it widens what the agent may do.
3. **Execution**: whether an agent using the built skill obeys those
   requirements in scenarios where they matter (planned; needs the frozen
   lists to pick scenarios).

Ground truth is a **human-reviewed, frozen** requirement list per source.
Without it the benchmark would grade a model against a model.

## Status (2026-11-20)

| Step | State |
|---|---|
| Corpus: 5 sources, 2,550 words | done (`sources/`) |
| Candidate requirement lists: 87 kept (88 lines), every quote verbatim in its source | AI-drafted, AI-reviewed twice (revision logs in each file); **awaiting human approval** (`review/`) |
| Freeze tool (`scripts/lab/fidelity_freeze.py`) | done |
| Preservation and introduction scorer (`scripts/lab/fidelity_score.py`) | done; smoke-tested on candidates only |
| Builds to score: `skillwren compile` and the skill, two models | after freezing |
| Execution scenarios | after freezing |

## Corpus

| Source | Shape | License | Origin |
|---|---|---|---|
| `code-reviewer` | review-only (read and search tools only) | MIT | `benchmarks/archive/skill-orig/` (Jeffallan) |
| `full-stack` | dense, ordering and authority heavy | the owner's | full-stack 0.2.0 prose |
| `webapp-testing` | tool ordering, branches | Apache-2.0 | anthropics/skills @ `e4bb5d96` |
| `theme-factory` | show, ask, confirm, then write | Apache-2.0 | anthropics/skills @ `e4bb5d96` |
| `internal-comms` | routing by type, ask when unclear | Apache-2.0 | anthropics/skills @ `e4bb5d96` |

Only each `SKILL.md` is in scope (and its license); referenced files are not.

## How to review (the human step)

Edit each file in `review/`: keep (`[x]`), drop (`[ ]`) or rewrite each line;
add what is missing with the next free ID; fill in `Reviewed by:` and `Date:`.
Then:

```text
py -3 scripts/lab/fidelity_freeze.py --validate   # quotes, IDs, kinds
py -3 scripts/lab/fidelity_freeze.py              # writes frozen/<source>.json
```

Freezing pins the source and review digests and refuses to overwrite a list
frozen from other bytes.
The frozen file also records the candidates' provenance (`candidate_provenance`):
AI-drafted and AI-reviewed lines become ground truth only through the
human reviewer named in the file.

## Enforcement tier per requirement

`skillwren coverage BUILT_SKILL.md --fidelity result.json [--policy P]` gives
each preserved requirement the tier of the element that preserves it:
enforced, recorded, instructed or unverifiable (SPEC 25). A requirement can
be faithfully translated and still only instructed; the two are reported
side by side, never merged.

## Scoring

```text
py -3 scripts/lab/fidelity_score.py <source> <built SKILL.md> [--out result.json]
```

A model judge (Sonnet) rates each requirement and must quote the built
skill; a quote not found verbatim makes the verdict `unverified`. Results
say which basis they used (frozen, with reviewer and date, or
`--candidates`, unreviewed). A sample of judgments goes back to the human
reviewer for spot-checking before any result is reported as measured.

Smoke test (candidates, unreviewed; not a result): Sonnet's 0.12.2
conversion of `code-reviewer` scored 22 preserved and 1 weakened of 23 (the
judge read "review only" as relying on the tool list without forbidding
commands), with 3 introduced constraints, none widening.
