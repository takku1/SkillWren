# Changelog

## Unreleased

- Patch versions are format-equivalent: `version: 0.4.1` validates
  against the format-0.4 validator; `0.5` still fails F1.
- New error T2: same-skill `run` arguments with known declared types
  must match the callee `accepts` entry type; unknown-typed bindings
  stay exempt.
- CLI: `check --all` (one-line summary per `*.md`, skips
  `benchmarks/archive/`) and `check --explain` (plain-language
  paragraph per error).
- New `docs/skill-template.md` one-file template (validates clean),
  referenced from the authoring guide.
- Benchmarks README notes the seeded synthetic secrets in
  `archive/target.py` and `archive/target2.py` (scanner false-positive
  record).

- Mutation middle ground: shared catalog (`tests/mutation_catalog.py`,
  15 skeleton + 9 golden one-break mutants), committed tripwire
  (`tests/test_mutations.py`, asserts beta-recall plus alpha-precision),
  and kill-matrix sweep (`tests/mutation_sweep.py`, beta gates,
  alpha advisory).
- Spec §11: same-skill `run` arguments are documented as optional
  overrides (omission is never an error); the sweep's one survivor was
  a bad mutant under this model, replaced by unbound-arg (U1) and
  bad-target (R3) mutants.
- Prune: benchmark round inputs and raw outputs moved byte-identical to
  `benchmarks/archive/`; summaries and READMEs stay up top.

## 0.4.1 (2026-10-01)

Follow-up seams, no format change:

- `for each` over a binding with a known non-`List` declared type is a
  type error (T1); `Any` and untyped bindings stay exempt pending
  dataflow type inference.
- Rebinding or writing the iterated collection inside the loop body is
  an error (L1, previously loop-variable-only).
- Spec §11 no longer claims cross-file arity/type validation; the W8
  unverified boundary is stated up front.
- Suite: 60 tests.

## 0.4.0 (2026-10-01)

Hardening release ("make the bird mean what it says"): no new expressive
features. The validator now parses flows into an indentation AST plus a
control-flow graph and enforces what v0.3 only described:

- Structure: `otherwise`/retry ownership (O1/L3), strict exactly-three-
  backtick fences, contract-before-logic body ordering, no prose between
  semantic blocks (F2).
- Authority: `require user ...` needs a dominating decision `ask`,
  decision asks need a following confirmation, bare confirmations need a
  preceding ask (A2, fully structural — word overlap stays warning-grade).
- Dataflow: per-path definite binding (U1: branch joins, failed reads bind
  nothing, `discard` unbinds), same-skill `run` binds only the callee
  flow's returned names, `apply` is pure and cannot name resources (E4).
- Safety: required inputs gated where used (R4), no mutation on any path
  to a dismissible ask (M1), read+write at one literal path declared
  under `mutates` (E2).
- Schemas: closed recursive types, kebab-case skill/flow ids, boolean
  flags, canonical `read+create` access, closed resource properties,
  positive budgets, numeric versions at or below the validator (F1/F2).
  Headers follow the strict SkillWren Frontmatter Profile (no tabs).
- Warnings: otherwise fall-through (W9), unreachable code (W10);
  cross-skill runs marked as unverified effect boundaries (W8);
  appendix requires a real heading (W4).
- Golden theme-factory repaired: accepted corrections are applied before
  retry, user decisions are asked, repair loops use `retry`, canonical
  access. Golden discipline documented: validator-clean plus
  semantic-reviewed plus scenario-tested.
- Suite: 58 tests with adversarial fixtures per rule, including
  path-sensitivity pins verified against the v0.3 engine.

## 0.3.0 (2026-10-01)

- Rebrand: the project is now **SkillWren** (`skillwren` package, `skillwren`
  CLI). Validator behavior is unchanged.
- Packaging: new `pyproject.toml` (setuptools, stdlib-only, `skillwren`
  console script), `LICENSE` (MIT), `.gitignore`.
- Layout: single doc set in `docs/` (drops the `docs/superpowers/specs` vs
  `src/` mirror); examples in `examples/`; benchmark evidence in
  `benchmarks/`; unit suite stays in `tests/`. Pruned exact-duplicate files
  (`test/pkg/SKILL.md`, mirrored spec set).
- CLI: `skillwren check <file>...` (exit 0 clean, 1 on errors), also
  available as `python -m skillwren check <file>...`.
- Spec: Section 15 now describes the shipped CLI surface; `--all` and
  `--explain` are deferred to a later release.
