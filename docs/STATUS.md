# Status

**Last Updated**: 2026-11-12

## Current Phase

Package 0.6.0, format 0.6. SkillWren now checks `logic` blocks wherever they
live: in complete SkillWren skills or as fragments in ordinary flow files,
which is how full-stack, its one long-term user, is built. Statically
checked and tested (172 tests, 31 mutants, 0 misses); effect on agent
behavior unmeasured.

## Active Focus

- Offer full-stack the fragment check and two upstream findings: an
  `order:` rule for the assurance screen (field report 3, G1) and the U1
  on `integration` in `flows/design.md`. Their adoption is their decision.
- Next build: compile order rules and `verify ... from` gates into runtime
  enforcement (host hooks or guard preconditions), SPEC Section 17 item 1.
- Next evidence: one controlled comparison with content held constant
  (prose versus checked fragments versus fragments plus enforcement),
  ideally as an added arm in full-stack's FS-016 harness.

## Architecture Summary

A stdlib-only Python package. `skillwren.validator` parses Markdown into
semantic blocks, builds an indentation AST and control-flow graph per flow,
and runs dataflow checks (definite binding, dismissal safety, authority
structure, effects, and 0.6 order rules) in one shared must-analysis
framework; a `Workspace` resolves `run <flow> from <file>` across files.
`compiler`, `metrics`, and `review` build and measure reviewed conversions;
`conform` runs a skill headless and compares final files, commands, and
asks with its declarations, optionally appending to a run log.

## Key Decisions

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
- `docs/archive/2026-10-05-full-stack-backfill/`: the BF-1 to BF-8 design,
  fully shipped in 0.5.0.
- Benchmark rounds 1-2 "attribution confirmed" wording: historical; see the
  October review for the narrower reading.

## Known Gaps

- No measured behavioral benefit of the format over equal-content prose.
- Order rules check the written procedure, not what the model does.
- Correlated branch conditions are not recognized (U1 false positives are
  possible, as on full-stack's `integration`).
- `build`/`measure` handle complete skills, not fragment sets.
- `check` budgets use `ceil(chars/4)`; exact counts only in `measure`.

## Documents

- `docs/current/SPEC.md` (normative), `authoring-guide.md`,
  `skill-template.md`, `fragment-template.md`, `compiler.md`,
  `language-design.md`
- `docs/current/design/`: `fragments-and-ordering.md`,
  `compact-conversion.md`
- `docs/current/research/`: `research-review-2026-11.md` (latest),
  `research-review-2026-10.md`

## Unreleased continuation: evidence auditing and ledger

The game-theory research and implementation begun in the Claude session
are present: W15, `check --audit`, shared evidence classification, command
dispatch refactoring, and `ledger start/exec/note/check/show`. The package
version remains 0.6.0 pending release; references to 0.7 in the research
note describe the planned release.

Validation: 183 unittest tests pass, including six ledger regressions for
argument forwarding, failed and successful evidence, strict self-report
checking, tampering, and missing commands. The ledger is an offline trace
checker, not runtime enforcement. Unrecorded actions, rewritten chains,
and tail truncation remain outside its guarantees.

## Runtime assurance work — 2026-11-12

Implemented: trusted-host guard, verifier/input/target binding, restart and
single-use evidence, retained checkpoints, audit coverage reporting, isolated
command observation, typed operation references, CI definition, scripted
A/B/C harness and short onboarding. See
`current/design/runtime-assurance.md` and `current/quickstart-runtime.md`.

The guard's reference deployment denies the agent direct protected mounts;
ordinary same-account Codex/Claude shells are not automatically confined.
The offline sandbox command is separate from networked Claude `conform`.
Model A/B/C runs await a model/provider and usage budget. Remote CI and branch
protection are not established merely by adding a workflow locally.
