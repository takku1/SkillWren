# SkillWren — logic-first skills (v0.3)

Skills written as logic instead of prose: a contract header for cheap,
headers-only routing plus a 16-verb logic body with gates, authority, effects,
and local recovery. Natural language describes meaning; formal structure
describes control.

## Layout

- `src/skillwren/` — shippable package: stdlib-only static validator plus
  `skillwren` CLI (`check`).
- `docs/` — `SPEC.md` (contract), `authoring-guide.md` (procedure, template,
  checklists).
- `examples/` — `theme-factory.golden.md` (worked golden example all tooling
  must accept), `code-reviewer.md` (trial conversion, installed as
  `code-reviewer-logic` in the benchmarks).
- `benchmarks/` — two blinded benchmark rounds with raw reports, frozen skill
  inputs, targets, and scoring.
- `tests/` — validator suite: fixtures plus `test_validator.py` (30 tests).

## Quickstart

Install (no dependencies, stdlib only):

```sh
pip install -e .
```

Validate a skill (exit 0 clean, 1 on errors):

```sh
skillwren check path/to/skill.md
```

Without installing:

```sh
PYTHONPATH=src python3 -m skillwren check path/to/skill.md
```

Run the suite:

```sh
python3 -m unittest tests.test_validator
```

## Evidence

Two blinded benchmark rounds, original prose skill vs logic rewrite on fresh
seeded targets each round: 8/8 recall both rounds both sides, zero false
positives; severity went 6/8 to 8/8 for logic after gating the rubric
(content-only change, clean attribution); skill context 5-8x smaller. See
`benchmarks/benchmark-report.md` and `benchmark-report-r2.md`.

## Status

v0.3 (2026-10-01). Known validator limitation: same-skill `run`
argument values are checked for boundness, not full type conformance (no
dataflow inference yet). Next frontier: EBNF grammar and constrained-decoding
profile (spec Section 17).

## License

MIT — see `LICENSE`.
