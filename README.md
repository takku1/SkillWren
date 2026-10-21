# SkillWren — logic-first skills (v0.5.0)

Skills written as logic instead of prose: a contract header for cheap,
headers-only routing plus a closed control vocabulary with gates, authority,
effects, and local recovery. Natural language describes meaning; formal
structure describes control.

## Layout

- `src/skillwren/` — shippable package: stdlib-only static validator plus
  `skillwren` CLI (`check`, `conform`).
- `docs/` — `SPEC.md` (contract), `authoring-guide.md` (procedure, template,
  checklists).
- `examples/` — `theme-factory.golden.md` (worked golden example all tooling
  must accept), `code-reviewer.md` (trial conversion, installed as
  `code-reviewer-logic` in the benchmarks).
- `benchmarks/` — two blinded benchmark rounds (summaries plus frozen
  `archive/` of round inputs and raw reports).
- `tests/` — validator suite: fixtures plus `test_validator.py` (89 tests),
  the mutation tripwire `test_mutations.py` over `mutation_catalog.py`
  (28 one-break mutants), and the `mutation_sweep.py` kill-matrix runner.

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

`check` is static and free. To see what a skill actually changes when it
runs, `skillwren conform` runs it once headless in a throwaway git
workspace and reports any file outside its resources' `glob:` patterns
(SPEC Section 14). It needs the Claude Code CLI and spends model usage:

```bash
skillwren conform path/to/SKILL.md --prompt "..." --model claude-sonnet-5-5 \
  --budget-usd 0.3 --workspace path/to/sample --auth-from-profile
```

Run the suite (92 tests):

```sh
python3 -m unittest tests.test_validator tests.test_mutations
```

## Evidence

Two blinded benchmark rounds, original prose skill vs logic rewrite on fresh
seeded targets each round: 8/8 recall both rounds both sides, zero false
positives; severity went 6/8 to 8/8 for logic after gating the rubric
(content-only change, clean attribution); skill context 5-8x smaller. See
`benchmarks/benchmark-report.md` and `benchmark-report-r2.md`.

## Status

v0.5.0 (2026-10-05). The validator parses flows into an indentation AST and a
control-flow graph and enforces repair ownership, ask/confirm structure,
required-input gates, full schemas, per-path binding, and dismissal safety.
Format 0.5 adds `else:` arms, `access: read+write`, optional `purpose` and
`release`, an `exec` action with `effects.executes`, `verify ... from`
evidence gates, and the `conform` runtime checker (SPEC Section 14).
Known limitations: same-skill `run` arguments with unknown types (from
`as`/`generate`/`run`) skip type conformance until dataflow inference
lands; cross-skill runs are an unverified effect boundary. Next frontier:
EBNF grammar and constrained-decoding profile (spec Section 17).

## License

MIT — see `LICENSE`.
