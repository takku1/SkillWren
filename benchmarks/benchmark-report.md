# Benchmark round 1: original vs logic-first code-reviewer

Date: 2026-10-01. Target: `target.py` (988 bytes). Full texts: `report-orig.md`
(14,681 bytes), `report-logic.md` (4,236 bytes). Token figures are
`ceil(chars/4)` per the spec fallback, labeled approximate.

## Setup

Two isolated runners, same target, each reading only its assigned skill.
Runner O (original prose skill + its `references/`, loaded per skill
instructions). Runner L (logic rewrite, `review-file` flow). Key held by the
parent only; neither runner saw it. Model for both: muse-spark-1.3-contributor.

Install: `muse skills validate` rejected the logic file until `description`
(plus `name`) was added to the frontmatter — spec Section 5 does not include
these keys (spec gap: installer-required frontmatter). Installed as
`code-reviewer-logic` (user scope) after the fix; original untouched.

## Key (8 seeds)

- S1 SQL injection, L14 — critical
- S2 hardcoded API key, L7 — critical
- S3 N+1 query loop, L35-36 — major
- S4 unescaped HTML / XSS, L26 — critical
- S5 `pickle.loads` on stored data, L27 — critical
- S6 magic number (literal `3`, `SHIPPED` unused), L25 — minor
- S7 swallowed exception (`except Exception: pass`), L22-23 — major
- S8 `requests.get` without timeout, L21 — major

## Per-seed results

| Seed | Key sev | Orig found | Orig sev | Logic found | Logic sev |
|------|---------|------------|----------|-------------|-----------|
| S1 SQLi | critical | yes | critical ok | yes | critical ok |
| S2 secret | critical | yes | critical ok | yes | critical ok |
| S3 N+1 | major | yes | major ok | yes | major ok |
| S4 XSS | critical | yes | critical ok | yes | **major MISS** |
| S5 pickle | critical | yes | critical ok | yes | critical ok |
| S6 magic # | minor | yes | minor ok | yes | minor ok |
| S7 swallow | major | yes | major ok | yes | major ok |
| S8 timeout | major | yes | major ok | yes | **minor MISS** |

Recall 8/8 both. Severity 8/8 original, 6/8 logic.

## Beyond the key

- False positives: 0 both.
- Bonus true positives (real, unseeded): original 6 (missing-user crash as
  critical, unclosed connections, positional column indexes, hardcoded db path,
  naming nit, missing docstrings); logic 2 (missing-user crash as major,
  unclosed connections).
- Praise: original 5 specific items; logic 0 (skill has no praise step).
- Author questions: original 5; logic 0 in report (2 WOULD-ASKs in META only).
- Test assessment: original yes; logic no (skill has no tests step).
- Fixes: original full before/after code blocks; logic one-liners.
- Verdict: both correct (Request Changes / Do not merge). Note the logic skill
  invents its own verdict wording — no taxonomy is specified.
- Runner slip (original): checklist marks "Error handling is meaningful" done
  while describing it as broken — verbatim in `report-orig.md`.
- Adherence traces: original hit 5 phases + checkpoints with 5 WOULD-ASKs;
  logic traced all 12 flow steps with all 3 gate outcomes and 2 WOULD-ASKs.
  The `verify every finding has quoted evidence` gate held: every logic
  finding quotes exact lines.

## Context cost

| | Original | Logic |
|---|---|---|
| Skill bytes loaded | 26,205 (SKILL.md 5,179 + 5 refs 21,026) | 3,081 (single file) |
| Skill tokens, approx | ~6,552 | ~771 (8.5x less) |
| Report bytes | 14,681 | 4,236 (3.5x shorter) |
| Runner usage in/out | 99,118 / 6,918 | 45,061 / 3,474 |

Usage totals include multi-turn context re-sends, so the skill-bytes row is
the clean comparison; both point the same way. The original's reference
loading (5 of 6 files, 21KB) is exactly the progressive-disclosure cost the
spec is designed to kill.

## Verdict

Format validated on recall-per-token: 8/8 seeds found with quoted evidence at
1/8.5th the skill context. Precision parity NOT yet claimed: severity 6/8 and
thinner report richness (no praise/questions/tests, fewer bonus finds, invented
verdict wording). All deltas trace to test-skill CONTENT — no severity rubric,
no report-shape requirements, thin appendix — not to format mechanics, which
executed as designed (12/12 steps traced, gates held).

## Follow-ups

1. Content pass on `test/skill.md`: severity rubric, report-shape requirements
   (praise/questions/tests/verdict taxonomy), richer appendix; then benchmark
   round 2.
2. Spec gaps to fold in: intra-skill `run` args, `system-may` exercised rule,
   mechanical effects coverage, installer frontmatter keys, write-never-read
   binding warning.
3. Skillcreator guidance: report-shape checklist for review-class skills.

## Limitations

N=1; single model; parent authored target + key and scored (bias risk — raw
reports preserved for audit); headless run (interactive steps simulated, not
exercised); usage totals confounded by turn count.
