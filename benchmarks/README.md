# Benchmarks (frozen evidence)

Two blinded rounds, original prose skill vs logic rewrite, fresh seeded
targets each round. Start with `benchmark-report.md`, then
`benchmark-report-r2.md` — the round summaries with keys, per-seed
scoring, and context-cost tables.

`archive/` holds the frozen round inputs and raw outputs, preserved
byte-identical for audit:

- `report-orig.md`, `report-logic.md`, `report-orig-r2.md`,
  `report-logic-r2.md` — raw runner outputs.
- `skill-orig/` — the prose skill plus its `references/` (round inputs).
- `skill-logic.md` — the frozen round-1 logic input (v0.1 header budget).
  It predates the v0.3 400-token header ceiling, so the current validator
  flags it (B1 error plus W5/W6 warnings); that is expected and the file
  stays byte-identical.
- `target.py`, `target2.py` — seeded review targets for rounds 1 and 2.

Note: `archive/target.py` and `archive/target2.py` contain intentionally
seeded synthetic secrets/keys as test fixtures for the benchmark rounds
(one of the planted review findings is a fake `sk-live-…` token). They
are not real credentials — secret scanners should treat hits there as
expected fixtures, not incidents.

Note: file paths quoted inside these frozen reports (`test/bench/...`,
`test/skill.md`, bare `report-*.md` / `target*.py` names) refer to the
pre-0.3.0 layout. The v0.3 logic skill they evaluate lives at
`examples/code-reviewer.md`.
