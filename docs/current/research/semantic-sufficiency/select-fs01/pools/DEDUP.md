# FS-01 deduplication

Method: `scripts/fs01_pool_check.py` normalizes each brief (title +
brief + attachment contents, lowercased, alphanumeric tokens of length
>= 3) and computes pairwise Jaccard similarity. Pairs at or above 0.45
are flagged for human adjudication; exact duplicate brief ids are hard
errors.

## Results (2026-11-18)

- 60 briefs, 0 pairs at or above the 0.45 flag threshold.
- Closest pairs at any similarity (spot-checked, all clear):

| Score | A | B | Adjudication |
|---|---|---|---|
| 0.30 | fs01-d-25 | fs01-i-25 | Deliberate cross-group mirror (same payments trap, design vs implement). Distinct deliverables. |
| 0.27 | fs01-d-08 | fs01-i-08 | Deliberate mirror (typed returns, design vs implement). Distinct tasks. |
| 0.25 | fs01-d-22 | fs01-i-18 | Deliberate mirror (cache stampede, design vs implement). Distinct tasks. |
| 0.23 | fs01-i-28 | fs01-i-30 | Shared file-operation vocabulary; different requirements (auth vs ordering). |
| 0.22 | fs01-d-14 | fs01-i-12 | Deliberate mirror (payment webhooks, design vs implement). Distinct tasks. |
| 0.20 | fs01-d-06 | fs01-i-01 | Both pagination; different scope (design policy vs implement endpoint). |

Highest same-group similarity is 0.19–0.20 (shared domain vocabulary:
cache, pagination, auth), well below threshold. Cross-group mirrors are
intentional: the same decision-sensitive trap family tested once as a
design brief and once as an implementation brief.

## Residual risk

Lexical similarity cannot detect paraphrased duplicates. Mitigation: all
60 briefs were authored in one session against a dimension plan with
pairwise review of the closest pairs above; the 0.45 threshold with
manual adjudication of the top pairs is the recorded control, not a
guarantee.
