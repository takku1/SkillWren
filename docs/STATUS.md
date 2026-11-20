# Status

**Last Updated**: 2026-11-19 (0.10 work; field-report response on branch `field-report-2026-11-19`)

## Current Phase

Package 0.9.0, piloted beta with real-host evidence. A real coding agent
(headless Claude Code) loads a packaged SkillWren skill from a one-line
request and leaves an evidence chain the host verifies independently.
The first model measurements are in: draft fidelity, an independent
corpus review, a 72-run skill-form comparison, and the model A/B/C
runtime comparison. Current verification results are recorded in CI.

## Active Focus

- Response to the full-stack field report of 2026-11-19
  ([design](current/design/field-response-2026-11-19.md),
  [three-tier results](current/research/field-response-2026-11-19.md)):
  exclusion rules (`never A before B`, P3), ledger package provenance
  (`--package` / `--loaded`), one typed-ID grammar (`validator/refs.py`).
  The work passes all three tiers: 404 tests, 33/33 spec mutants and
  14/14 code mutants killed, and live Sonnet runs. In those runs, agents
  read P3 correctly 3/3 but fixed it minimally 0/3, and provenance caught
  a stale copy 3/3.

- Empirical sufficiency selector: `skillwren select` evaluates a fixed
  candidate-router set under the frozen v23 router-certification spec:
  declared authority/dependency sets, simultaneous risk bounds, worst-cell
  loss, optional CVaR and DS tiers, invariant-verification and evidence-reuse
  gates, fallback-ranked certificates, a verified refusal router when
  nothing is admissible (otherwise it abstains), and optional cell weights
  mapping the objective to the deployment distribution. Verdicts are
  study-admissible, never deployment-certified. The deployment bridge
  (`skillwren certgate`) binds those certificates to artifact bytes,
  regime, and config before a trusted host authorizes execution.
  [Formulation](current/research/semantic-sufficiency/FORMULATION.md)
  and [notes](current/research/semantic-sufficiency/NOTES.md) preserve the
  user's broader model; deficiency estimation, adaptive search and regret
  guarantees remain research work. The historical main run and its
  preregistered decision rule are unchanged.

- NL compiler ([design](current/design/nl-compiler.md)): `skillwren compile`
  turns full-context prose into checked SkillWren via a requirement
  inventory (every source line accounted for), anchored lowering, bounded
  check/repair, and an explain-and-judge pass, emitting a generated review
  map. Built with `check --json`, `skillwren inventory`, a stub-driven
  offline suite, and a Claude adapter. First runs
  ([results](current/research/nl-compiler/README.md)): full-stack's last
  prose package compiles valid with every line accounted for; judge drops
  3 -> 0 after prompt rules; remaining issue is over-asking; inline output
  is ~5x the prose entry per activation. Dogfood compile of the SkillWren
  skill found two real ambiguities in its source (fixed).
- 0.10 work merged to `main` (PR #2; `next-0.10` is behind `main`): corpus
  v2 (frozen), drafter evidence check and prompt 2 (requirement defects
  19 -> 7 on v2), runtime benchmark protocol 2 (written up in
  `model-evaluation-plan.md`), inline-form example. Package version is
  still 0.9.0; the 0.10 release has not been cut.
- Still open, needs a decision or resources: a task hard enough to
  separate skill forms; an OS-isolated host run (the agent needs
  credentials inside the isolated account or container); a human review
  of corpus v2 and the drafts.
- full-stack PR takku1/full-stack#1 (typed return anchors) awaits that
  project's review.

## Architecture Summary

A stdlib-only Python package. `skillwren.validator` parses Markdown into
semantic blocks, builds an indentation AST and control-flow graph per flow,
and runs dataflow checks (definite binding, dismissal safety, authority,
effects, order rules) in one must-analysis framework; `workflow` renders the
AST as deterministic prose or a versioned dump, `approve` binds approval to
exact bytes, and `draft` proposes through an adapter that cannot approve.
`guard` binds each write to an administrator policy, pinned verifiers and
exact verified bytes; `sandbox`, `audit` and `ledger` observe, checkpoint
and check recorded runs. `build` packages single-file skills or fragment
sets; `compile` and `inventory` turn prose into checked skills through a
model adapter with per-requirement accounting; `scripts/` holds the
real-host harness, adapters, and model-measurement tools.

## Key Decisions

- 2026-11-19: exclusion rules are an `order:` form (`never A before B`)
  and not `exec` preconditions: no new statement syntax, and they bind
  every caller through `run`. Composition written in prose stays out of
  static reach; the ledger checks the same rule on traces.
- 2026-11-19: package identity is a tree digest over every file (not
  only Markdown) so hook drift counts; a mismatch fails `ok` but leaves
  the order verdict `valid` separate.
- 2026-11-18: NL-to-SkillWren compilation is organized around a
  per-requirement inventory checked mechanically (every source line
  covered, every requirement landed), because measured draft loss is
  silent requirement drops, not invented permissions. No new syntax;
  approval stays human.
- 2026-11-17, 0.9: one source of truth for the agent. Real agents followed
  logic-only, prose-only and both forms equally (72/72); with both, they
  executed the prose and never read the flow. Recommended form: logic and
  contract blocks inline in SKILL.md plus a step-to-command table.
- 2026-11-17, 0.9: typed returns (`return #id`) anchor flow exits; returns
  of one exit may share an ID. `exec readonly` is a declared claim that M1
  skips, enforced only by `ledger exec --readonly`.
- 2026-11-17, 0.9: ledger steps named as typed references match their
  rules (the documented pattern was silently unexercised before).
- 2026-11-17, 0.9: correlated branch conditions stay unrecognized by
  design. Inferring them from natural language is unsound; nest the
  dependent step or use an explicit verifier. Full-stack fixed its one case.
- 2026-11-17: the robust value-of-information rule for choosing clarifying
  questions is not adopted. Drafter questions covered 9 of 22 real
  defects and 7 were silent, so ranking the existing questions cannot
  reach the main loss (`research/game-theory-2026-11.md`).
- 2026-11-17: model reviews are labelled as such; corpus bytes stay
  frozen and fixes go into a re-frozen v2.
- 2026-11-12, 0.8: explanation is deterministic from the AST; approval
  confirms intended meaning, not formal equivalence.
- 2026-11-12, 0.7: deployment is proved by topology; crash recovery fails
  closed; CI lanes pinned and all 14 required on `main`.
- 2026-10-21: claims narrowed to three separate layers (static validity,
  reviewed preservation, observed behavior).

## Deprecated/Legacy

- Hand-maintained prose copies of a skill's logic: superseded by the
  inline-logic form (measured, no benefit, drift risk).
- Inline JSON adapter arguments as the only form: plain argv after `--`.
- Header-only routing as a goal (SPEC Section 9): kept as a convention.
- `src/skillwren/validator.py` single module: replaced by the package.
- Benchmark rounds 1-2 "attribution confirmed" wording: historical.

## Known Gaps

- P3's repair hint did not lead live agents to the minimal fix (move the
  effect after the later step); 2/3 stopped to ask. P3 cannot see
  composition written in prose. Provenance needs the caller to name the
  host-loaded path.
- NL compiler: one run per arm, model judge only, no human review of
  compiled output; over-asking persists; fragment layout unmeasured.
- Every real-agent run complied, so the form comparison hit a ceiling;
  it shows no harm from either form, not a benefit.
- Model drafts silently drop about a third of the requirements they lose;
  approval remains a human step.
- Reviews of the corpus and drafts are by model sessions, not humans.
- Model A/B/C (90 trials): zero unauthorized write attempts in every arm,
  so enforcement value against a cooperating model is unmeasured; the
  prose arm's 4/30 completion comes from an unstated candidate format,
  and the protocol needs fixing before any syntax claim.
- The host demo shares one OS account between agent and host; isolation
  is proved separately (`scripts/isolation_probe.py`).
- Order rules check the written procedure, not what the model does.

## Documents

- `docs/current/SPEC.md` (normative, Section 21 for 0.9),
  `authoring-guide.md`, `skill-template.md`, `fragment-template.md`,
  `compiler.md`, `language-design.md`, `quickstart-runtime.md`
- `docs/current/design/`: fragments and ordering, compact conversion,
  runtime assurance, independent review response
- `docs/current/research/`: `skill-adoption-readiness.md` (gate),
  `host-demo/`, `skill-forms/`, `nl-fidelity/` (corpus, `model-draft/`,
  `independent-review/`), `model-evaluation-plan.md` and
  `runtime-model*.json*` (A/B/C), `lifecycle/`, `game-theory-2026-11.md`,
  research reviews, field reports
