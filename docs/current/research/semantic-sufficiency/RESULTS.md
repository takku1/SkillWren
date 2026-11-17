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

Wait for provider capacity before retrying. The original launch command
was recovered from Claude session `299fd589-f751-474b-b56d-99157159d3f2`:
source `Z:/vulnscanner`, five repetitions, five workers, all eight ablations
and seven text files. The source's HEAD and reflog identify commit
`3b47485c6c96191f98efd09b8bd4f3a4b6556e5a` (April 3, 2026), with no later
HEAD movement recorded. Local uncommitted source changes are irrelevant
because setup uses `git clone`; they were not included in the subjects.
This is recovered provenance, not a source hash captured by the original
harness. Verify that source HEAD still matches before running:

```powershell
$textArgs = @()
Get-ChildItem examples/sufficiency/forms/*.md, examples/sufficiency/lingua/*.md | ForEach-Object {
    $textArgs += '--text'
    $textArgs += "$($_.BaseName)=$($_.FullName)"
}
py -3 scripts/sufficiency_lab.py --source Z:/vulnscanner --variants 'full,-readonly,-blocked,-report,-nofake,-final,-readonly-blocked,-readonly-blocked-nofake-final' @textArgs --models haiku,sonnet --reps 5 --resume
```

Do not substitute another source or rewrite the tested forms. Resume is
serial regardless of `--jobs` to avoid queuing more usage-limit failures.

The follow-up has not rerun paid model calls or modified the existing
attempts. The external `takku1/full-stack#1` remains for the user's review.
