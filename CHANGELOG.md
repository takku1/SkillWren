# Changelog

## 0.8.0 (2026-11-12)

Authoring pipeline plus field-report fixes.

- `skillwren explain-workflow`: deterministic plain-language meaning of a
  flow derived from the AST only -- steps, branches, order rules,
  authority, effects, enforcement eligibility, and cross-file run targets.
- `skillwren approve`: human approval bound to the exact file digest, with
  enforceable-operation coverage against a guard policy; `approve --check`
  fails when the file changed since approval.
- `skillwren draft`: proposal-only workflow drafting through a model
  adapter (intent in, flow plus assumptions and unresolved questions out).
  The proposal still needs `check`, `explain-workflow`, and human approval.
  `--adapter-file` reads the adapter argv from a file for shells that
  cannot pass inline JSON.
- AST dump (`dump_workflow`, `DUMP_VERSION = 1`): versioned serialization
  with line provenance and an explicit/inferred split.
- NL fidelity corpus: 26 hand-authored intent-to-flow pairs in
  `docs/current/research/nl-fidelity/` with reviewer protocol and
  regression facts pinned by tests.
- Ledger: `exec --cwd`, `exec --readonly` (sandbox-verified, digest-pinned
  image, fails closed on writes), `note --detail` (milestones still match
  step names exactly), and `ledger attempt` for tries that satisfy nothing.
- Authoring guide: record-a-step-when-it-completes and
  separate-reproduction-from-acceptance patterns from live use.
- Fixes from the full-stack field report: `__version__` aligned to the
  package version; `--help` exits 0; CLI help test coverage.

## 0.7.0 (2026-11-12)

Runtime assurance release. The static 0.6 checker is unchanged in behavior;
the new work is enforcement, isolation, and evidence.

- Guard: trusted-host `Controller` (`src/skillwren/guard.py`) binds each
  operation to an administrator policy, pinned verifier programs, the
  candidate content digest, and an unchanged target; approvals are restart-
  and single-use. Crash recovery fails closed on a trailing intent; symlink
  and hardlink target swaps are denied; approvals never cross instances.
- Sandbox: `skillwren sandbox` runs a command in a disposable, networkless,
  read-only container copy of a workspace and reports undeclared file
  changes; the image must be pinned by digest. Separate from networked
  Claude `conform`.
- Audit: `skillwren audit` checks a linear event log against an
  independently retained checkpoint; truncation, resealing, and log/
  checkpoint divergence are rejected; interrupted sessions are reported.
- Ledger: `check` now reports `valid` (invariants and order hold),
  `completeness` (`complete`/`incomplete`/`unassessed`/`violations`), and
  `outcome`. `check --require-completeness` fails unassessed runs, so
  assurance CI can require an explicit milestone contract.
- Deployment proof: `tests/test_deployment.py` runs an adversarial agent in
  a container with no protected mounts while the guard runs on the host;
  direct access is unavailable and only verify-then-write mutates the
  target.
- Evaluation: `scripts/benchmark_runtime.py` supports paired A/B/C runs
  with per-arm rates, 95% confidence intervals, and a comparison caveat.
  Scripted run: 90 paired trials (`docs/current/research/runtime-ab-
  comparison.jsonl`), C arm 0 unauthorized writes and 0 false blocks.
  Model arms are pending a provider and usage budget; see
  `docs/current/research/model-evaluation-plan.md`.
- Tests: 211 (crash recovery, concurrency, deployment, ledger semantics,
  benchmark summary); 1 skip where the OS denies symlink creation.
- Docs: README leads with the runtime controller; `STATUS.md` updated;
  CI runs the 3.9 lane on ubuntu-24.04 (setup-python ships no 3.9 build
  for Ubuntu 26.04).

## 0.6.0 (2026-11-12)

From full-stack field report 3 and the 2026-11 research review
(`docs/current/research/research-review-2026-11.md`). Format 0.6 is
additive: 0.5.x files keep validating.

- Fragments: `skillwren check --fragment` checks `logic` blocks embedded in
  ordinary Markdown flow files (optional frontmatter and contract, prose
  anywhere, foreign code fences ignored, prose anchors `apply` steps).
  Full-stack's flow files were rejected by 0.5 and now check;
  `flows/implement.md` is clean and `flows/design.md` shows one U1
  (`integration`), reported upstream.
- Cross-file runs: `run <flow> from <file> with:` resolves beside the file
  and up to the skill root; returns bind in the caller, a mutating callee
  counts for M1, and unresolvable targets are R3.
- Order rules: contract `order:` entries (`<earlier> before <later>`) and
  error P1 when a path reaches the later step without the earlier one
  completing. Failed gates establish nothing; runs count when the callee
  guarantees the step on every return. Reproduces field report 3's G1.
- Contract `inputs:` for fragments (strict U1); otherwise inputs are
  inferred from unbound and presence-tested names. `check --summary`
  prints them.
- Warnings W13 (order rule never applies) and W14 (fragment without
  logic). `check` flags may appear in any order; unknown flags are usage
  errors.
- SPEC: `exec` command text is an argument list without a shell (D3);
  goals reordered so header routing is an optional convention; research
  grounding adds procedure-following and runtime-enforcement work; new
  Section 20; Section 17 re-ranked around enforcement and a controlled
  comparison.
- `conform`: allows `python`, `python3`, and `py`; launches the resolved
  `claude` path; reports commands and fails undeclared ones;
  `--record DIR` appends a JSONL run log including errors.
- Refactor: `validator.py` split into the `skillwren.validator` package
  with a shared must-dataflow solver and a `FlowAnalysis` class; every
  diagnostic on every fixture, example, and mutant compared before and
  after.
- Tests: 172 (fragment suite, conform additions, template check);
  mutation catalog gains a fourth base with three P1 mutants (31 total,
  0 misses).
- Docs: `docs/STATUS.md`; active docs moved to `docs/current/`, the
  shipped backfill design to `docs/archive/2026-10-05-full-stack-backfill/`;
  new fragment template, design note, and research review; authoring
  guide gains flow files, order rules, and mistakes 23-25.

Also first released here (developed after 0.5.0):

- Optimization workflow (no format change): `measure` and `build --original/--review`
  add hash-bound manual requirement review, exact cl100k_base token or
  character comparison, archived originals/review in the manifest, and a
  strictly-smaller expanded-prompt gate. Plain `build` and context imports
  remain packaging only. `conform` now validates the skill first, snapshots
  final file state independently of Git, and treats failed sessions as
  errors. New examples/optimization and skills/skillwren conversion skill.
- Docs and explain refresh (no format change): `check --explain` now
  prints a plain-language paragraph for warnings (W1–W12) as well as
  errors, pinned by a coverage test over every code the validator can
  emit; README and authoring guide aligned to 0.5.0 (version, test and
  mutant counts, Status); SPEC Section 17 pruned of shipped BF items;
  the 0.5.0 release is cut below.

## 0.5.0 (2026-10-05)

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

## Pre-0.7.0 development trail (all items shipped in 0.7.0 above)

- Evidence auditing (`check --audit`) and W15 for self-reported ordering
  prerequisites, informed by the game-theory research note.
- Runtime ledger with command execution, artifact hashes, captured
  order rules, strict evidence checking, and chained records.
- CLI dispatch refactor and share evidence classification across checks.
- Child arguments preserved after `ledger exec --`; cover the parser fix
  and ledger semantics with six regression tests.

- Policy-bound `guard` controller with fixed verifiers, exact candidate
  hashes, target-version binding, single-use approvals and restart revocation.
- Independently retained audit checkpoints and recorder-session checks.
- Offline Docker `sandbox` effect observer and real isolation probes.
- Exact typed ordering references and duplicate-ID diagnostic P2.
- Runtime mutation tests, randomized scripted A/B/C trials, a trusted
  model-adapter interface, a Linux/Windows CI matrix, and wheel smoke tests.
- Static validity, mechanism tests, deployment assumptions and model
  reliability measurements explicitly separate.




