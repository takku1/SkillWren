# Status

**Last Updated**: 2026-11-17 (0.10 work in progress)

## Current Phase

Package 0.9.0, piloted beta with real-host evidence. A real coding agent
(headless Claude Code) loads a packaged SkillWren skill from a one-line
request and leaves an evidence chain the host verifies independently.
The first model measurements are in: draft fidelity, an independent
corpus review, a 72-run skill-form comparison, and the model A/B/C
runtime comparison. Current verification results are recorded in CI.

## Active Focus

- Empirical sufficiency selector: `skillwren select` evaluates a fixed
  candidate-router set under the frozen v23 router-certification spec:
  declared authority/dependency sets, simultaneous risk bounds, worst-cell
  loss, optional CVaR and DS tiers, invariant-verification and evidence-reuse
  gates, fallback-ranked certificates, a verified refusal router when
  nothing is admissible (otherwise it abstains), and optional cell weights
  mapping the objective to the deployment distribution. Verdicts are
  study-admissible, never deployment-certified. [Formulation](current/research/semantic-sufficiency/FORMULATION.md)
  and [notes](current/research/semantic-sufficiency/NOTES.md) preserve the
  user's broader model; deficiency estimation, adaptive search and regret
  guarantees remain research work. The historical main run and its
  preregistered decision rule are unchanged.

- 0.10 in progress on branch `next-0.10`: corpus v2 (frozen), drafter
  evidence check and prompt 2 (requirement defects 19 -> 7 on v2), runtime
  benchmark protocol 2, inline-form example. Release after the protocol-2
  A/B/C result is written up.
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
sets; `scripts/` holds the real-host harness and model-measurement tools.

## Key Decisions

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
