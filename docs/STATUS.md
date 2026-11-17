# Status

**Last Updated**: 2026-11-17

## Current Phase

Package 0.9.0, piloted beta with real-host evidence. A real coding agent
(headless Claude Code) loads a packaged SkillWren skill from a one-line
request and leaves an evidence chain the host verifies independently.
The first model measurements are in: draft fidelity, an independent
corpus review, a 72-run skill-form comparison, and the model A/B/C
runtime comparison. 246 tests pass.

## Active Focus

- Corpus v2: fix the four reference-flow defects the independent review
  found (pairs16 f17, pairs21 f22, 05, unrequested existence gates),
  re-freeze under a new manifest, rerun model drafts.
- Drafter evidence lint: warn or fail when a drafted gate loses its
  `exec` evidence, the main class of silent requirement loss (3 of 7).
- A task hard enough to separate skill forms (every form complied in
  every run so far), an OS-isolated host run with a real agent, and a
  fixed A/B/C protocol (state the candidate format; score retry-after-
  failed-gate separately from abort).
- Optional upstream note for full-stack: typed returns could replace its
  prose rule `exec assurance table check before return`. Its adoption is
  its decision.

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
