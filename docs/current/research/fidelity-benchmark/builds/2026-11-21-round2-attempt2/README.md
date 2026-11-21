# Round 2: compiler only, anchor fix (2026-11-21)

One variable changed from round 1: the I13 anchor fix of SkillWren 0.13.3
(a command and its re-runs in its gate's repair are one step). The I7
evidence rule is unchanged. Pinned at `f1a87b4` (clean tree), Sonnet for
every call, five compiler builds, run once, $2.31. Attempt 1 at the same
commit died on a usage limit in every build (`../2026-11-21-round2/`) and
was rerun whole.

| Source | Round 1 (0.13.2) | Round 2 (0.13.3) |
|---|---|---|
| code-reviewer | refused: 3x I7, 3x I13 | refused: 2x I7 |
| full-stack | refused: 1x I7 | refused: 4x U1 |
| webapp-testing | refused: U1 | **published** (exit 1: open items, "Not approved"; the judge's WT-3 "gated on usage" finding was overturned in adjudication) |
| theme-factory | refused: P1, 1x I7 | refused: 3x I7 |
| internal-comms | refused: 4x I7, I5, I9 | refused: 4x I7, I9 |
| Published | 0/5 | 1/5 |

## Reading (before adjudication)

- **I13 is gone.** It appeared only in round 1's code-reviewer compile;
  no round 2 build reports it. That is the one change attributable to the
  fix.
- **I7 still blocks three of five** (code-reviewer, theme-factory,
  internal-comms), as expected with the evidence rule unchanged.
- **The other differences are not attributable to the fix.** webapp-testing
  failed in round 1 on U1, which the fix does not touch, and full-stack now
  fails on U1 where round 1 failed on I7. With one model run per cell,
  these move with model variation; publishing 1/5 instead of 0/5 is not
  evidence that the fix improved publication.

## Scores

`scores/`: the five artifacts scored once against the frozen AI-reviewed
baseline (Sonnet judge, $0.20): webapp-testing as published, the other
four as refused drafts (diagnostic). The 12 doubtful judgments were
AI-adjudicated (ChatGPT, GPT-6, relayed by the owner, 2026-11-21: 6 agree,
6 overturn) in `scores/*.adjudication.md`, then published:

```text
py -3 scripts/lab/fidelity_report.py scores/compiler-webapp-testing.json --coverage scores/compiler-webapp-testing.coverage.json --out report-compiler-published.json
py -3 scripts/lab/fidelity_report.py scores/compiler-{code-reviewer,full-stack,theme-factory,internal-comms}.json --coverage scores/compiler-{code-reviewer,full-stack,theme-factory,internal-comms}.coverage.json --out report-compiler-diagnostic.json
```

Results and reading: `RESULTS.md`.
