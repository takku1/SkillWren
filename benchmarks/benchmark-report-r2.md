# Benchmark round 2: gated rubric + report shape (content-only delta)

Date: 2026-10-01. Fresh target: `target2.py` (887 bytes, file-share API).
Full texts: `report-orig-r2.md`, `report-logic-r2.md`. Token figures are
`ceil(chars/4)`, labeled approximate. Round 1: `benchmark-report.md`.

## What changed between rounds (logic skill only)

Content pass, no spec changes: every finding now cites the severity rubric and
must pass `verify every finding carries a rubric severity` (with
otherwise→correct→retry); new praise/questions generation steps; report must
pass `verify report contains summary, findings, praise, questions, tests
note, and verdict` with an exact verdict taxonomy (Approve / Request Changes
/ Comment); appendix gained the rubric, report shape, and a category sweep.
Original skill byte-identical across rounds. Skill grew 3,081 → 5,339 bytes.

## Key (8 fresh seeds)

- T1 command injection (`shell=True`), L13 — critical
- T2 MD5 password hashing, L23 — critical
- T3 path traversal, L10 — critical
- T4 unbounded `SELECT *` + `fetchall()`, L33 — major
- T5 mutable default arg, L30 — major
- T6 missing-key crash (`request["email"]`), L22 — major
- T7 weak randomness for token, L18 — major (boundary probe)
- T8 magic number (`role == 2`), L32 — minor

## Per-seed results

| Seed | Key sev | Orig found | Orig sev | Logic found | Logic sev |
|------|---------|------------|----------|-------------|-----------|
| T1 cmdi | critical | yes | critical ok | yes | critical ok |
| T2 MD5 | critical | yes | critical ok | yes | critical ok |
| T3 traversal | critical | yes | critical ok | yes | critical ok |
| T4 unbounded | major | yes | **minor MISS** | yes | major ok |
| T5 mutdefault | major | yes | major ok | yes | major ok |
| T6 keycrash | major | yes | major ok | yes | major ok |
| T7 weakrand | major | yes | **critical MISS** | yes | major ok |
| T8 magic# | minor | yes | minor ok | yes | minor ok |

Recall 8/8 both. Severity: logic 8/8, original 6/8 — the round-1 gap flipped
on a fresh target with a content-only change.

## Beyond the key

- False positives: 0 both.
- Bonus true positives: original 5 (caller-controlled role/auth-bypass as
  critical — the sharpest find of the round, which logic missed; unclosed
  connections; username-ignored; magic bounds; unused `os` import), logic 4
  (unclosed connections, unbounded write, missing docstrings, unused params).
- Logic's auth-bypass miss is real: it graded `role == 2` as a magic number
  only, while the original saw caller-controlled authorization. Candidate
  appendix line for v0.3 content: sweep trust boundaries / caller-controlled
  authority, not just code patterns.
- T7 nuance: the original's critical for brute-forceable + unbound tokens is
  defensible; the key's major follows the rubric's explicit weak-randomness
  bucket. The rubric may want a brute-forceability escalation rule — open
  question for v0.3, not rescored here.
- Severity inversions on unseeded finds (upload limits: logic major vs
  original minor) show both runners reasoning, not parroting.
- Praise/questions/tests/verdict-taxonomy: logic now matches the original's
  report shape section for section (3 praise, 4 questions, tests note, exact
  "Request Changes").
- Gates: logic traced 18/18 steps; all 5 gates passed, including both new
  gates with no correction passes needed. Every finding cites its rubric
  bucket — visibly different behavior from round 1, where no finding cited
  any severity rationale.
- Original loaded the same 5/6 references with 6 WOULD-ASKs.

## Context cost

| | Original | Logic |
|---|---|---|
| Skill bytes loaded | 26,205 (same as round 1) | 5,339 (was 3,081) |
| Skill tokens, approx | ~6,552 | ~1,335 (4.9x less) |
| Report chars | 13,863 | 8,446 (1.6x shorter) |
| Runner usage in/out | 99,297 / 6,085 | 45,500 / 4,160 |

The content pass cost +2.3KB and bought severity parity-plus and full report
richness. Accuracy-per-byte is the metric that matters, and it moved the
right way on both axes.

## Verdict

Attribution confirmed: round-1 deltas were content, not format. With the
rubric enforced as a gate rather than printed as reference, logic went 6/8 →
8/8 severity on unseen seeds with no over-grading on the boundary probe, while
holding 8/8 recall, zero false positives, and the evidence gate. The format
thesis — gates beat prose — now has two rounds of evidence.

## Follow-ups (v0.3 queue)

1. Apply the six banked spec amendments (spec Section 19).
2. Rubric: brute-forceability escalation rule (T7 nuance).
3. Appendix: trust-boundary / caller-controlled-authority sweep line (auth-bypass miss).
4. Consider round 3 on a third target after v0.3 lands.

## Limitations

Same harness caveats as round 1: N=1 per round, single model, parent-authored
keys and scoring (raw reports preserved for audit), headless WOULD-ASK
simulation, usage totals confounded by turn count.
