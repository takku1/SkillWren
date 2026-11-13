# NL fidelity corpus: reviewer protocol

26 natural-language workflow descriptions with hand-authored SkillWren
equivalents: `01`–`05`, batches `pairs06/11/16` (5 flows each), and
`pairs21` (6 flows: f21ingest/f21store plus f22–f25). The 25-pair
milestone is met with one spare.

## How to review

1. Read one `*-intent.md` only.
2. Read the `explain-workflow` output for the matching flow file
   (`skillwren explain-workflow --fragment <file>`). Do not read the
   flow file itself.
3. Write down the requirements, branches, permissions, and limitations
   you recover.
4. Compare against `*-facts.json`: every fact should be recoverable.
   Anything you recovered that is not in the facts, or any fact you
   could not find, is a finding against the explainer (or the flow).

## Status

Author-reviewed only. Independent review and the model-draft
reproduction test (draft from intent, compare against the approved
flow, count added/dropped requirements) are pending.

## Reserved converter regressions

The full-stack live-use field report
(`../full-stack-live-use-2026-11-12.md`) documents converter-grade
defects a future automatic translator must preserve or flag: two M1
dismissal-safety violations, the conditional assurance screen, the
missing stack check, and the early return that skipped the final
check. Keep these cases as regression material for skill translation;
do not absorb them into this corpus without noting their origin.
