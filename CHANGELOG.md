# Changelog

## 0.12.0 (2026-11-20)

- The `skillwren` skill builds skills. It now creates a new skill from a
  request as well as converting an existing `SKILL.md`: requirement
  inventory, user confirmation of the inventory before any file is
  written (dismissal-safe, M1), draft, check-and-repair loop, requirement
  landing check, deterministic explanation, `build`. The skill is written
  in SkillWren (inline form) and checks clean with no warnings; its
  language card (`references/language.md`) carries a worked example that
  CI checks.
- Installable without pip: `plugin/` is a self-contained Claude Code
  plugin (skill, language card, full references, and the checker bundled
  as `lib/`, standard library only). `/plugin install skillwren
  --marketplace takku1/SkillWren`; other hosts copy `plugin/skillwren/`.
  `scripts/build_plugin.py` generates it from `skills/skillwren/`,
  `src/skillwren/` and `docs/current/`; `--check` (in the test suite)
  fails when it is stale. Plugin files are LF on every checkout
  (`.gitattributes`).
- `.agents/skills/skillwren` is now a pointer to `skills/skillwren/`
  instead of a second, drifting copy.
- Live proof (`docs/current/research/skill-build-live/`): a headless
  agent with only the plugin built a new skill from a one-line request.
  Turn 1 showed the inventory and wrote nothing; after "confirmed", the
  built skill checked clean with no warnings ($0.25, one task, one model).

## 0.11.1 (2026-11-20)

- Package identity ignores line endings in text files: a tree digest
  hashes text (no NUL byte) with CRLF normalized to LF, and `ledger start
  --package` compares the flow copy the same way. Found releasing
  full-stack 0.9.0: the installed plugin (CRLF checkout) and the
  repository (LF) held one commit but 27 files differed byte for byte, so
  `close` would report a false package mismatch. Binary files stay
  byte-exact. Digests recorded by 0.10.0-0.11.0 for CRLF text change.
  One more code mutant (31/31).

## 0.11.0 (2026-11-20)

- Skill-load assurance (SPEC 24): a guard policy may require
  `skill: {name, tree_sha256, loads}`; with `guard --run-id ID`, every
  protected operation is denied unless the host-owned `loads` file holds an
  unambiguous load of that skill, with that tree digest, in this run. It
  fails closed on unreadable or malformed records and is rechecked
  immediately before a write commits. Policies without `skill` are
  unchanged. It proves a host-recorded load under the trusted-host
  assumptions, not adherence.
- `ledger record-load --out FILE` writes load records to a host-owned
  file instead of the agent's working directory. `--package DIR` records
  the directory the host loaded (a plugin hook's
  `${CLAUDE_PLUGIN_ROOT}/<skill>`) instead of resolving the name; from
  full-stack field report 5, whose hook records its own copy.
- Pipeline check (rebuild full-stack, build in MochiOS, feed back):
  [full-stack live use 2026-11-20](docs/current/research/full-stack-live-use-2026-11-20.md).
- Tests: `tests/test_guard_skill_load.py` (26), nine new code mutants in
  `tests/field_mutation_sweep.py` (29/29 killed).

## 0.10.0 (2026-11-20)

- Response to the full-stack field report of 2026-11-19 (design note
  `design/field-response-2026-11-19.md`, three-tier report
  `research/field-response-2026-11-19.md`):
  - Exclusion rules: `order:` entries `never A before B`, new error P3, a
    may-analysis that binds the declaring file and every flow that runs its
    flows, so two fragments that are each clean cannot be composed into a
    runtime deadlock unseen. `ledger check` applies them to the trace
    (attempts count); `build` refuses a set with P3; the guard lists them
    as unenforced (SPEC 23).
  - Package provenance: `ledger start --package DIR` records a tree digest
    over every file and refuses a flow file that differs from the
    package's copy; `ledger check --loaded DIR` fails as
    `package-mismatch` when the host-loaded copy differs. `build`
    manifests carry `tree_sha256`.
  - One typed-reference grammar (`validator/refs.py`) shared by P2, order
    matching, the ledger, return parsing and `explain-workflow`; the
    renderer had accepted `#Deps` and `#de_ps`, which the validator ignores.
  - Authoring guide: exclusion rules, package binding, required entry
    milestones for fragments that must not be skipped, one grammar per
    shared identifier.
  - Tests: `tests/test_field_2026_11_19.py` (tier 1), two exclusion
    mutants in the catalog and `tests/field_mutation_sweep.py` (14 code
    mutants, tier 2), `scripts/lab/field_live.py` with the
    `examples/field-live/` skills (real agents, tier 3).
  - P3's repair hint now names the earliest conflicting statement (and,
    for a `run`, the effect inside the callee) and says to move it after
    the later step. Live rerun: 2 of the 2 agents that could keep checking
    applied that fix, against 0/3 with the old hint.
  - W16: a file names, outside `run`, another file with exclusion rules,
    so P3 cannot check that composition.
  - `skillwren ledger record-load`: a Claude Code `PostToolUse(Skill)` hook
    that records which copy of a skill the host loaded, with its digest at
    load time; `ledger check` uses it when `--loaded` is not given.
  - The workflow guard enforces `never A before B` when both steps are
    policy operations (refuses B once A has run; a failed check counts).
  - Live harness: temporary directories no longer carry the arm name
    (it cued skill use and invalidated the first skip results); new
    `skip-hidden` arm and `--invoke` flag. Rerun: an unrequired stack step
    was entered 0/6, a required one 6/6, and a requirement hidden in a host
    wrapper was recovered 6/6 after `ledger check` named it.

- NL compiler: `skillwren compile` turns a full-context prose source into
  a checked skill through a phased model adapter (inventory, lower,
  repair, judge), with a bounded repair loop and no publication on
  failure (`nlcompile.py`, design in `design/nl-compiler.md`).
  `scripts/adapters/claude_compile.py` is the Claude adapter; a scripted
  stub drives the offline tests.
- `skillwren inventory`: requirement inventories with source spans,
  line-coverage, landing (placement by kind, demanded evidence) and a
  generated `review.json`. Review maps accept `non_requirements` with a
  reason.
- `check --json`: machine-readable diagnostics plus unbacked verify gates.
- `build DIR` now checks an inline-form `SKILL.md` that holds logic
  blocks (it was skipped, so an inline skill with errors built).
- Benchmark corpus `research/nl-compiler/full-stack-0.2/`: full-stack's
  last prose package and its hand conversion, frozen. First runs and a
  dogfood compile of `skills/skillwren/SKILL.md` in
  `research/nl-compiler/README.md` (valid output, every source line
  accounted for, judge drops 3 -> 0 after lowering-prompt rules).
- `compile` re-judges a candidate after a judge-driven repair, so the
  manifest verdict is for the published bytes.
- `skills/skillwren/SKILL.md`: fragment sets are built; an unshrinkable
  candidate is packaged plainly with the tradeoff reported (both found by
  compiling the skill with itself).
- NL fidelity corpus v2 (`docs/current/research/nl-fidelity-v2/`), derived
  from frozen v1 by `scripts/make_corpus_v2.py`: fixes the four defects
  the independent review found (pairs16 f17, pairs21 f22, 05, unrequested
  existence gates); every flow checks clean and all 86 facts are pinned
  by tests, including the manifest digests. v1 stays frozen.
- Evidence check for drafts: `skillwren draft` lists `verify` gates that
  cite no `exec`/`read`/`open` result (the model's own judgment);
  `approve` records them as `unbacked_verifies` and warns.
  (`evidence.unbacked_verifies`.)
- Drafter prompt 2 (`scripts/adapters/claude_draft.py`, default): evidence,
  typed-ID, return and input rules; the repair round feeds back unbacked
  verifies. On v2: requirement defects 19 -> 7, silent ones 8 -> 3,
  valid after repair 6/9 -> 8/9, questions asked 36 -> 18 (one run).
- `fidelity_eval.py`/`corpus_review.py` take `--corpus`; `fidelity_eval`
  takes `--prompt`.
- Runtime benchmark protocol 2: the task states the candidate format, and
  trials count failed gates and whether the model continued after one.
- `examples/host-demo/dep-audit` now ships the recommended inline form as
  its `SKILL.md`; the experiment variants moved to `forms/`, and
  `host_demo.py --forms` defaults to `inline`.
- `.gitattributes` pins digest-bound files (frozen corpora, approved
  flows, lifecycle evidence) byte-exact on every checkout.
- Empirical DPCC selector (`skillwren select`, schema 2): per-regime
  studies with operational and decision-sufficiency tiers, fallback-ranked
  portfolios, per-candidate certificates with fallback links, an
  evaluator-attested (not proved) deficiency bound, invariant-verification
  gating, evidence-reuse modes (fresh/split/adaptive), and a verified
  refusal-only router when nothing is admissible. Verdicts are
  study-admissible, never deployment-certified; optional cell weights map
  the objective mean to the deployment distribution. Regime
  classification, the runtime monitor, and the certified router remain
  deployment-side work.
- Deployment bridge (`skillwren certgate`): binds selection certificates
  to artifact bytes, regime, and config, including every fallback member;
  denies tampered reports, altered artifacts, and context mismatches. A
  verified refusal router yields `refuse` (exit 3), never authorization;
  monitor and policy are caller-asserted inputs. Coordinated whole-report
  rewrites remain out of scope without signatures.
- Guard DPCC enforcement: a write operation's `dpcc` section re-verifies
  a fresh gate allow on every write (report recomputed from the hosted
  study, no verdict files) and only writes the selected artifact bytes;
  monitor completion, altered evidence, refusal, or abstention deny. The
  monitor re-runs against the deployed bytes; evidence digests are
  snapshotted at verification and confirmed at commit; hashed reports
  require bound study bytes.

## 0.9.0 (2026-11-17)

Real-host evidence and the first model measurements.

- Real-host demo (`scripts/host_demo.py`, `examples/host-demo/dep-audit`):
  headless Claude Code loads a packaged skill from a one-line request on
  a disposable clone of a real repository; the host then checks approval,
  ledger completeness with the order rule satisfied by evidence, the
  audit checkpoint, protected bytes, and denies replay and blocked
  submissions. Clean and blocked variants pass
  (`docs/current/research/host-demo/`). `--forms`/`--prompts` compare
  skill forms; 72 runs in `docs/current/research/skill-forms/`.
- Language (SPEC Section 21): typed return anchors (`return #id ... as
  ...`, `return #id:`), so order rules can constrain flow exits; returns
  of one exit may share an ID. `exec readonly ...` declares an
  observation that M1 does not count as a mutation; the explainer marks it
  as a claim enforced only by `ledger exec --readonly`.
- Ledger: a step named as a typed reference (`verify#deps`) now matches
  its rule. Before, only statement text matched, so the documented
  pattern left rules unexercised (found by the host demo).
- Explainer: `retry` names the gate it re-runs; gates without `otherwise`
  state the spec's default failure (found by the independent review).
- `build DIR` packages a fragment-set skill (every logic fragment checked,
  all files carried, manifest with digests); `measure` accepts
  directories and counts every Markdown file a host could load.
- `draft` and `scripts/benchmark_runtime.py` take the adapter as plain
  words after `--`, so no JSON quoting is needed on any shell; the
  benchmark gains `--adapter-file` and `--resume`.
- Model adapters for headless Claude Code: `scripts/adapters/
  claude_draft.py` (drafting) and `claude_runtime.py` (runtime trials).
- Measurements: model-draft reproduction over the frozen corpus
  (`scripts/fidelity_eval.py`), independent corpus review
  (`scripts/corpus_review.py`), question coverage of draft defects
  (`scripts/question_coverage.py`), and the model A/B/C runtime comparison
  (90 trials: no unauthorized write attempted in any arm; the prose arm's
  low completion is a protocol artefact, see `model-evaluation-plan.md`).
- Lifecycle `explanation.txt` files re-encoded from UTF-16 to UTF-8
  (content unchanged; they had been saved through a PowerShell redirect).

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




