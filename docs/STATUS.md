# Status

**Last Updated**: 2026-11-12

## Current Phase

Package 0.8.0, authoring pipeline beta. New in 0.8: deterministic
`explain-workflow`, digest-bound `approve`, proposal-only `draft`,
versioned AST dump, a 26-pair NL fidelity corpus, ledger `cwd` /
`readonly` / `detail` / `attempt` support, and field-report fixes
(version alignment, `--help` exit 0). 231 tests pass. Model comparison
and independent corpus review are pending.

## Active Focus

- Independent review of the NL fidelity corpus and the model-draft
  reproduction test (draft from intent, count added/dropped requirements
  against the approved flows).
- Run the model A/B/C comparison per
  `docs/current/research/model-evaluation-plan.md` (needs a provider and
  a usage budget); scripted arms alone cannot speak to model behavior.
- Confirm the full GitHub Actions matrix goes green on push and enable
  required status checks on `main` (a repository setting, not code).
- Offer full-stack the fragment check and two upstream findings: an
  `order:` rule for the assurance screen (field report 3, G1) and the U1
  on `integration` in `flows/design.md`. Their adoption is their decision.

## Architecture Summary

A stdlib-only Python package. `skillwren.validator` parses Markdown into
semantic blocks, builds an indentation AST and control-flow graph per flow,
and runs dataflow checks (definite binding, dismissal safety, authority
structure, effects, and order rules) in one shared must-analysis
framework. `workflow` renders the AST as deterministic prose or a
versioned dump with line provenance; `approve` binds human approval to
exact bytes; `draft` proposes through an adapter that cannot approve.
`guard` is a single-process controller that binds each write to an
administrator policy, pinned verifiers, exact approved bytes, and an
unchanged target, with single-use approvals and fail-closed crash
recovery; the embedding host must deny the requester direct access to
protected files, policy, verifiers, and checkpoints. `sandbox` observes
one command in a disposable networkless container, `audit` holds a linear
event log against an independent checkpoint, and `ledger` checks recorded
runs as valid, complete, or unassessed.

## Key Decisions

- 2026-11-12, 0.8: explanation is deterministic from the AST; the same
  model never both drafts and explains, and approval confirms intended
  meaning, not formal equivalence.
- 2026-11-12, 0.8: ledger milestones still match step names exactly; a
  separate `detail` field carries criteria. Attempts are a distinct
  record type ignored by checks. Read-only exec is sandbox-verified,
  not declared.
- 2026-11-12, 0.8: P2 IDs are document-scoped and unique per operation,
  which forced distinct verify/write IDs in the fidelity corpus.
- 2026-11-12, 0.8: the full-stack live-use report is kept as
  converter-regression material, not absorbed into the corpus.
- 2026-11-12, 0.7: ledger reports `valid` separately from `completeness`
  (`complete`/`incomplete`/`unassessed`/`violations`);
  `check --require-completeness` fails unassessed runs.
- 2026-11-12, 0.7: CI keeps the Python 3.9 lane on ubuntu-24.04;
  action tags are pinned to immutable SHAs.
- 2026-11-12, 0.7: deployment is proved by topology: the adversary runs
  in a digest-pinned container with no protected mounts while the guard
  runs on the host.
- 2026-11-12, 0.7: crash recovery fails closed on a trailing audit
  intent; approvals never cross processes.
- 2026-11-12, 0.6: the checked unit is the `logic` block; the header and
  header routing are optional conventions.
- 2026-11-12, 0.6: `order:` rules (P1) use must-analysis per flow entry;
  failed gates establish nothing.
- 2026-11-12, 0.6: `exec` command text is an argument list without a shell.
- 2026-11-12: validator split into a package; equivalence checked by
  comparing every diagnostic before and after.
- 2026-10-21: claims narrowed to three separate layers (static validity,
  reviewed preservation, observed behavior); reviewed compact conversion.

## Deprecated/Legacy

- Header-only routing as a goal (SPEC Section 9): kept as a convention.
- `src/skillwren/validator.py` single module: replaced by the package.
- "Runtime evidence (unreleased)" framing: the runtime shipped in 0.7.0.
- Stale `Unreleased`/`Experimental` changelog tails: folded into release
  sections as development-trail history.
- Benchmark rounds 1-2 "attribution confirmed" wording: historical.

## Known Gaps

- No measured behavioral benefit of the format over equal-content prose at
  model level (scripted enforcement only); model-draft fidelity unmeasured.
- Order rules check the written procedure, not what the model does.
- Correlated branch conditions are not recognized (U1 false positives are
  possible, as on full-stack's `integration`).
- `build`/`measure` handle complete skills, not fragment sets.
- Static M1 still counts read-only execs as mutations; no declared
  read-only flow syntax yet (runtime `ledger exec --readonly` exists).
- Remote CI has not yet run the fixed matrix; required status checks on
  `main` are not enabled.

## Documents

- `docs/current/SPEC.md` (normative), `authoring-guide.md`,
  `skill-template.md`, `fragment-template.md`, `compiler.md`,
  `language-design.md`
- `docs/current/design/`: `fragments-and-ordering.md`,
  `compact-conversion.md`, `runtime-assurance.md`,
  `independent-review-response.md`
- `docs/current/research/`: `full-stack-live-use-2026-11-12.md` (latest),
  `model-evaluation-plan.md`, `nl-fidelity/` (corpus + protocol),
  `research-review-2026-11.md`, `research-review-2026-10.md`
- `docs/current/quickstart-runtime.md` (guard walkthrough)
