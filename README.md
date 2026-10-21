# SkillWren — logic-first skills (v0.5.0)

Convert an original SKILL.md into a tighter logical SKILL.md for an LLM.
Preserve operative rules and context; archive the original outside the prompt.
The compiler checks authored conversions, not automatic semantic equivalence.

A contract header enables cheap,
headers-only routing plus a closed control vocabulary with gates, authority,
effects, and local recovery. Natural language describes meaning; formal
structure describes control.

## Layout

- `src/skillwren/` — shippable package: stdlib-only static validator plus
  `skillwren` CLI (`check`, `measure`, `build`, `conform`).
- `docs/` — `SPEC.md` (contract), `authoring-guide.md` (procedure, template,
  checklists), `compiler.md` (measurement, review, and packaging).
- `examples/` — `theme-factory.golden.md` (worked golden example all tooling
  must accept), `optimization/` (reviewed conversion), and `context-build/`
  (literal context packaging).
- `benchmarks/` — two blinded benchmark rounds (summaries plus frozen
  `archive/` of round inputs and raw reports).
- `tests/` — validator suite: fixtures plus `test_validator.py` (89 tests),
  the mutation tripwire `test_mutations.py` over `mutation_catalog.py`
  (28 one-break mutants), and the `mutation_sweep.py` kill-matrix runner.
- `skills/skillwren/SKILL.md` — reusable procedure for converting and checking
  an original skill.

## Quickstart

Install (checking and plain builds use the standard library; exact token metrics are optional):

```sh
pip install -e '.[tokens]'
```

Validate a skill (exit 0 clean, 1 on errors):

```sh
skillwren check path/to/skill.md
```

Measure and build a reviewed conversion:

```sh
skillwren measure examples/optimization/original.md examples/optimization/SKILL.md
skillwren build examples/optimization/SKILL.md --out built-skill \
  --original examples/optimization/original.md \
  --review examples/optimization/review.json
skillwren check built-skill/SKILL.md
```

An optimized build requires a strictly smaller expanded prompt and a complete,
hash-bound review map. The map checks review bookkeeping, not semantic parity.
Exact cl100k_base tokenization may download its vocabulary on first use;
`--metric characters` is a separately labeled offline alternative. There is no
estimate fallback or universal compression target. See the
[compiler guide](docs/compiler.md) and reusable
[conversion skill](skills/skillwren/SKILL.md). Plain builds and literal context
imports remain optional packaging operations, not compression.

Without installing:

```sh
PYTHONPATH=src python3 -m skillwren check path/to/skill.md
```

`check`, `measure`, and `build` do not invoke models. Independent local field
trials can use any available agent; the optional Claude adapter below is not
required. To see what a skill actually changes when it
runs, `skillwren conform` runs it once headless in a throwaway git
workspace and reports any file outside its resources' `glob:` patterns
(SPEC Section 14). It needs the Claude Code CLI and spends model usage:

```bash
skillwren conform path/to/SKILL.md --prompt "..." --model claude-sonnet-5-5 \
  --budget-usd 0.3 --workspace path/to/sample --auth-from-profile
```

Run the complete offline suite:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Evidence

Two pilot benchmark rounds compared an original prose skill with a logic
rewrite: both found 8/8 seeded issues in each round, and the rewrite loaded
roughly 5-8x fewer bytes of skill context. Content and targets also changed,
so these observations do not isolate a causal benefit of the syntax or prove
behavioral equivalence. See `benchmarks/benchmark-report.md` and
`benchmark-report-r2.md` for the original reports and their limitations.

The [research review](docs/research-review-2026-10.md) examines the evidence,
formal-analysis boundaries, runtime faults, and a controlled evaluation design.
The [language direction](docs/language-design.md) and
[conversion design](docs/design/compact-conversion.md) distinguish static
validity, reviewed rule preservation, and measured behavior. Optimize cost per
verified change: include wrong turns and repair loops, not only load tokens.

`conform` compares file contents before and after a successful session,
including ignored files and edits to the installed skill. It preserves the
workspace's `.gitignore` and excludes copied Git metadata. It returns 2 for
failed/incomplete sessions or environment errors; `--json` emits one JSON
document with a `conforms` Boolean. This is a final-state observer, not a
sandbox: transient/reverted changes, external effects, and Git metadata are
outside its observations. Project/host configuration can still affect runs.

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
