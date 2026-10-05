# Changelog

## Unreleased

- BF-8: `skillwren conform` runs a skill headless and reports undeclared
  mutations against new optional resource `glob:` patterns, plus asks that
  were followed by changes. Opt-in; spends model usage.

- Format 0.5 (BF-6, BF-7): `else:` arms, `access: read+write`, optional
  `purpose`, optional `release`, `exec ... from ... as ...` with
  `effects.executes`, and `verify ... from <name>`. 0.4.x files keep
  validating. Mutation catalog gains `else` and `exec` bases (28 mutants,
  0 misses).

- BF-5: new warning W12 for `apply` specs with no appendix anchor; golden
  examples gain step-meanings lists.

- BF-4: SPEC says what hosts actually read (§1, §9, §16) and where runtime
  guarantees come from (§8); four live-use patterns in the authoring guide.

- BF-3: SPEC §12 distinguishes confirmed, declined (repair runs), and
  dismissed (zero mutation, including headless hosts); template wording
  fixed; guide mistake 22.

- BF-2: a declared `budget.header` above 400 is B1; a declared
  `budget.body` above 2500 warns (new W11). Matches SPEC §10.

- BF-1 (full-stack backfill): unquoted `[ ] { }` members inside inline
  header collections are F1 errors because YAML parsers reject them and
  hosts then drop the header. The SPEC example and the theme-factory
  golden are quoted; a PyYAML conformance test covers every clean header.

- Docs: budget ceilings clarified as tokens not bytes (guide plus
  template note), side-by-side `-logic` piloting documented, two
  live-fire lessons added to Common mistakes. No validator change.
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
- MochiOS live-fire docs (no validator change): derive-before-ask
  recipe, optional-resource guard pattern, multi-agent `always`
  recipe, `apply` appendix-anchoring rule (guide Common mistakes
  20-21, new checklist item); SPEC Goal 2 qualified (transform prose
  is advisory); single-actor effects boundary stated (§8); optional
  resources listed as future work (§17).

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
