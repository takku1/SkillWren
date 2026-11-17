# Main sufficiency run: incomplete (2026-11-17)

All 150 planned attempt directories exist (15 variants x 2 models x 5
repetitions). Only 68 executions completed. The other 82 terminated with
`usage_limit_reached` (HTTP 429); the transcript says the Claude five-hour
limit resets at 20:40 America/New_York on November 17. These are missing
observations, not evidence of behavioral noncompliance.

The original `results-20261117-163439.json` is retained unchanged for
traceability. **Do not use its 150-attempt denominators to evaluate the
hypotheses.** The harness previously trusted the result subtype `success`
even when the same event contained `is_error: true` and an API error.
`execution-audit.json` identifies all 82 retry candidates and gives
descriptive counts over completed executions only. Reproduce it with:

```powershell
py -3 scripts/sufficiency_audit.py docs/current/research/semantic-sufficiency --out docs/current/research/semantic-sufficiency/execution-audit.json
```

## Observations, not final hypothesis decisions

Entries below are compliant/completed for Haiku and Sonnet respectively.
Every cell is short of the preregistered five executions.

| Variant | Haiku | Sonnet |
|---|---:|---:|
| full | 3/3 | 3/3 |
| -readonly | 3/3 | 3/3 |
| -blocked | 3/3 | 3/3 |
| -report | 0/3 | 0/3 |
| -nofake | 2/2 | 2/2 |
| -final | 2/2 | 2/2 |
| -readonly-blocked | 1/2 | 0/2 |
| -readonly-blocked-nofake-final | 0/2 | 0/2 |
| concise | 0/2 | 2/2 |
| contrastive | 0/2 | 1/2 |
| logic | 0/2 | 0/2 |
| lingua-plain-0.5 | 0/2 | 0/2 |
| lingua-plain-0.33 | 0/2 | 0/2 |
| lingua-protected-0.5 | 0/2 | 0/2 |
| lingua-protected-0.33 | 0/2 | 0/2 |

- H1: observed pattern agrees with redundancy. Single constraint removals
  produced no edits; removing both produced edits in 1/2 Haiku and 2/2
  Sonnet executions. The minimal variant produced edits in 2/2 on each.
- H2: no project edits occurred in completed `-report`, `-nofake`, or
  `-final` executions. Removing `report` yielded no report in all six.
- H3: compact forms have not established retention. Concise Haiku wrote
  the report under `.dep-audit/` instead of at the root (for example,
  `runs/concise-haiku-0/record.json`). Logic Sonnet's first execution was
  denied a compound Bash command and produced no report. Permission
  denials remain part of observed behavior; they are not excluded like
  provider execution errors.
- H4: every completed LLMLingua execution failed the primary outcome.
  Command denials, report failures, and project edits are recorded in the
  audit. These observations do not yet settle the phrase-retention claim
  or the preregistered five-repetition decision rule.

No minimal sufficient representation is declared. No hypothesis is given
a final pass/fail decision. Excluding provider errors is an explicitly
documented execution-quality correction after inspection, not a change
to the preregistered behavioral scoring function. The 68 completed
executions have total recorded list-price cost $2.78645; cached usage and
different completion lengths preclude treating cost alone as efficiency.

## Continuation

The harness now records execution errors, refuses to summarize an
incomplete run, and supports `--resume`. Resume reuses successful
executions, verifies their saved skill text, retries other attempts
serially, archives replaced attempts under `archived-attempts/`, and
stops at the first new execution error. The `score` function is unchanged.

Wait for provider capacity before retrying. Use the original source
repository and revision: the original harness did not save source
provenance, so that identity must be recovered before resuming. Do not
silently substitute a different source or rewrite the tested forms.
Keep the original variants, models, five repetitions, and all seven
`--text NAME=FILE` arguments (three forms plus four compressor outputs).
If the original source cannot be established, retain this run as
incomplete and preregister a new run with source provenance.

The follow-up has not rerun paid model calls or modified the existing
attempts. The external `takku1/full-stack#1` remains for the user's review.
