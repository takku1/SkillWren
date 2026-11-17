# Model-draft reproduction test (2026-11-17)

Harness: `scripts/fidelity_eval.py` (drafting through `skillwren draft`
with `scripts/adapters/claude_draft.py`), plus `scripts/question_coverage.py`.
Drafter: Sonnet 5.5, given the authoring guide and fragment template only,
no tools, no repository. Judge: Opus 5.5 in a separate session. Inputs: the
nine frozen intent files (26 flows), digests checked against `../FROZEN.md`
before each run. Cost: $0.26 drafting, $0.41 judging, about $0.10 coverage.

## Results (`sonnet/results.json`)

| Measure | Value |
|---|---|
| Drafts passing `check` first time | 5/9 files |
| ... after one repair round with the check errors | 6/9 (01, pairs06, pairs16 still invalid) |
| Statements dropped / added vs reference (structural, 142 reference) | 33 / 21 |
| Order rules dropped / added (13 reference) | 3 / 10 |
| Judged requirements dropped / added / changed | 18 / 4 / 12 |
| Corpus facts in the draft's explanation (strict text, IDs abstracted) | 46/83 |

Check failures were mechanical: bare `return`, flows that fall off the end,
contract sections out of order, a missing `as` on `exec`, one P1.

## What the judged defects are

Of 34 judged defects, 12 are mechanism-only: the step still happens but
lost its stable ID, so the guard cannot bind it. The model typed only the
steps an order rule referenced. The 22 requirement defects split three ways:

- 9 would have been exposed by answering one of the drafter's own
  questions;
- 14 were disclosed in its assumptions (some are both);
- 7 were silent. Three of the seven drop the evidence step behind a gate
  (the verify no longer cites an `exec` result), two lose structure inside
  a retry loop or an ordering between two asks, one adds an unrequested
  gate, one loses the audience of a `show`.

Two "changed" verdicts (pairs16 f17, pairs21 f22) favour the draft: the
independent review found those reference flows wrong against their intents
(see `../independent-review/README.md`). Judged counts therefore overstate
model error somewhat.

## Answer to the readiness question

"Can an AI draft a skill without silently inventing permissions?" No new
permission was invented: added items were existence gates and one abort.
Silent requirement loss is the real risk (7 of 22 defects, about a third),
and it concentrates in evidence: drafts gate on the model's own reading
instead of a recorded check. `check --audit` already shows each gate's
evidence class; making the drafter run it (or failing approval when a
reference-style `verify ... from <exec>` becomes a self-report) is the
cheapest next fix. Approval stays a human step.
