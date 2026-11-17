# Model drafts on corpus v2: prompt 1 vs prompt 2 (2026-11-17)

Same harness as v1 (`scripts/fidelity_eval.py --corpus .../nl-fidelity-v2`),
Sonnet 5.5 drafting, Opus 5.5 judging, one repair round. Prompt 1 is the
0.9 drafter prompt. Prompt 2 (`scripts/adapters/claude_draft.py`,
`SW_DRAFT_PROMPT=2`) adds five rules aimed at the defect classes the v1
run found: every check is an `exec` judged by `verify ... from` it; every
`verify` and `write` gets a typed ID; no bare `return`; no invented
existence gates (declare `inputs:`); repair loops re-check before `retry`.
With prompt 2 the repair round also feeds back unbacked verifies, which
`skillwren draft` now reports. One run per prompt over 9 files (26 flows):
read the direction, not the exact size.

| Measure | Prompt 1 | Prompt 2 |
|---|---|---|
| Valid first time / after one repair | 3/9 / 6/9 | 3/9 / 8/9 |
| Judged dropped / added / changed | 11 / 4 / 9 | 5 / 1 / 4 |
| Requirement defects (not ID-only) | 19 | 7 |
| ... silent (no question, no assumption) | 8 | 3 |
| Questions asked | 36 | 18 |
| Unbacked verifies, first draft / final | 2 / 1 | 0 / 0 |
| Order rules dropped / added (structural) | 4 / 8 | 3 / 6 |
| Corpus facts in the explanation (strict text) | 56/86 | 55/86 |
| Drafting cost | $0.40 | $0.45 |

Compared with v1 under prompt 1 (18 / 4 / 12 judged), the prompt-1 row
here is already lower, partly because v2's references no longer carry
the four defects the independent review found (on v1 the judge counted
those as model drift).

Takeaways: the evidence rule worked on the first draft without needing the
repair feedback; the remaining silent defects (3) are structural (an
ordering between two asks, a write moved into a branch, one dropped
abort). Strict fact recall did not move because it is wording-sensitive
(abort messages, flow names); the judged counts are the semantic measure.
The default drafter prompt is now 2.
