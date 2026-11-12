# Status

**Last Updated**: 2026-11-12

## Current Phase

Package 0.7.0, runtime-assurance beta. The static 0.6 checker is unchanged;
new in 0.7: trusted-host guard controller, isolated sandbox observer,
checkpointed audit log, and ledger completeness contracts. 211 tests pass
(1 OS-privilege skip). Scripted enforcement measured (90 paired trials:
guarded arm 0 unauthorized writes, 0 false blocks); model comparison and
remote CI confirmation are pending.

## Active Focus

- Run the model A/B/C comparison per
  `docs/current/research/model-evaluation-plan.md` (needs a provider and a
  usage budget); scripted arms alone cannot speak to model behavior.
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
framework. `guard` is a single-process controller that binds each write to
an administrator policy, pinned verifiers, exact approved bytes, and an
unchanged target, with single-use approvals and fail-closed crash
recovery; the embedding host must deny the requester direct access to
protected files, policy, verifiers, and checkpoints. `sandbox` observes one
command in a disposable networkless container, `audit` holds a linear event
log against an independent checkpoint, and `ledger` checks recorded runs
offline as valid, complete, or unassessed.

## Key Decisions

- 2026-11-12, 0.7: ledger reports `valid` (invariants and order hold)
  separately from `completeness` (`complete`/`incomplete`/`unassessed`/
  `violations`); `check --require-completeness` fails unassessed runs so
  assurance CI requires an explicit milestone contract.
- 2026-11-12, 0.7: CI keeps the Python 3.9 lane on ubuntu-24.04 because
  setup-python ships no 3.9 build for Ubuntu 26.04 (13 other lanes stay on
  ubuntu-latest); action tags are pinned to immutable SHAs.
- 2026-11-12, 0.7: deployment is proved by topology, not by code import:
  `tests/test_deployment.py` runs the adversary in a digest-pinned
  container with no protected mounts while the guard runs on the host.
- 2026-11-12, 0.7: crash recovery fails closed — a trailing audit intent
  refuses restart until the host reconciles the real output; log/checkpoint
  divergence is rejected; approvals never cross processes.
- 2026-11-12, 0.6: the checked unit is the `logic` block; the header and
  header routing are optional conventions (full-stack D-017 evidence: hosts
  read only `name`/`description`; the header cost ~400 tokens per run).
- 2026-11-12, 0.6: `order:` rules (P1) use must-analysis per flow entry;
  failed gates establish nothing; runs count when the callee guarantees the
  step on every return.
- 2026-11-12, 0.6: `exec` command text is an argument list without a shell
  (field report 3, D3).
- 2026-11-12: validator split into a package; equivalence checked by
  comparing every diagnostic before and after.
- 2026-10-21: claims narrowed to three separate layers (static validity,
  reviewed preservation, observed behavior); reviewed compact conversion.

## Deprecated/Legacy

- Header-only routing as a goal (SPEC Section 9): kept as a convention, not
  a reason to add a header; no host implements it.
- `src/skillwren/validator.py` single module: replaced by the
  `skillwren.validator` package (same public names).
- "Runtime evidence (unreleased)" framing: the runtime shipped in 0.7.0;
  the ledger section is now "offline", model arms remain pending.
- `docs/archive/2026-10-05-full-stack-backfill/`: the BF-1 to BF-8 design,
  fully shipped in 0.5.0.
- Benchmark rounds 1-2 "attribution confirmed" wording: historical; see the
  October review for the narrower reading.

## Known Gaps

- No measured behavioral benefit of the format over equal-content prose at
  model level (scripted enforcement only).
- Order rules check the written procedure, not what the model does.
- Correlated branch conditions are not recognized (U1 false positives are
  possible, as on full-stack's `integration`).
- `build`/`measure` handle complete skills, not fragment sets.
- `check` budgets use `ceil(chars/4)`; exact counts only in `measure`.
- Remote CI has not yet run the fixed matrix; required status checks on
  `main` are not enabled.

## Documents

- `docs/current/SPEC.md` (normative), `authoring-guide.md`,
  `skill-template.md`, `fragment-template.md`, `compiler.md`,
  `language-design.md`
- `docs/current/design/`: `fragments-and-ordering.md`,
  `compact-conversion.md`, `runtime-assurance.md`,
  `independent-review-response.md`
- `docs/current/research/`: `model-evaluation-plan.md` (latest),
  `research-review-2026-11.md`, `research-review-2026-10.md`
- `docs/current/quickstart-runtime.md` (guard walkthrough)
