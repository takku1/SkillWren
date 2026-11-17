# Skill adoption readiness (0.9.0 gate)

Assessment after the three lifecycle proofs (see `lifecycle/a-manual`,
`lifecycle/b-drafted`, `lifecycle/c-converted` with `outcomes.md` in
each). Tiers: [R] repository-verifiable (rerun the commands),
[S] self-reported (single-operator session logs), [U] unrated (no
evidence yet). Nothing here upgrades scripted or single-session results
into general reliability. Maturity: piloted beta for the pipeline
mechanics; concept stage for adoption claims. Next gate: a packaged
lifecycle skill loaded by a real coding agent against a disposable
repo, with ledger/guard evidence.

## Answers

Tiers: lifecycle executions are [S] (single-operator logs) except the
parts rerunnable from the repo ([R]: `check`, `explain-workflow`,
`approve --check`, ledger replays, guard denials); all adoption and
model-behavior claims are [U].

**Can a user turn an existing agent skill into a SkillWren-formatted
skill without losing important requirements?** Mostly, with review.
The independent evidence-review conversion preserved all six
requirement areas but silently dropped four appendix-level details
(severity rubric, independent-oracle criterion, explicit no-findings
statement, unexecuted-tests note). The loss was caught only by
comparing against the shipped conversion. Conversion without a
requirement-by-requirement map and a comparison oracle loses detail
silently.

**Can an AI draft a skill without silently inventing permissions?**
Structurally yes: the draft adapter cannot approve, and `approve`
records coverage gaps (`#deps`, `#coverage`, `#evidence` uncovered in
all three lifecycles). But the stub invented structure (placeholders),
which the human had to replace. Measured 2026-11-17 with a real model
(`nl-fidelity/model-draft/README.md`): no permission was invented, but
of 22 requirement defects across 26 drafted flows, 7 were silent (no
question, no stated assumption), mostly gates that lost their evidence
step. Drafts passed `check` 5/9 first time, 6/9 after one repair.

**Can a user understand exactly what the converted skill does?**
Largely: `explain-workflow` states steps, branches, order rules,
authority, effects, enforcement eligibility, and cross-file targets,
plus what it cannot show (prose meaning of untyped steps, correlated
conditions). An independent model reviewer recovered 82/83 corpus facts
from explanations alone. Terminal steps can be order-anchored since 0.9
(`return #id`), and the explainer now states what `retry` re-runs.

**Can the packaged skill be invoked by a real coding agent against a
repository?** Yes, demonstrated 2026-11-17 [R, rerunnable with
`scripts/host_demo.py`]. Headless Claude Code, given one sentence and no
command hints, discovered and loaded `dep-audit` from a disposable clone
of a real repository, recorded check and verify as ledger evidence,
wrote through the guard, and left a chain the host verified
independently (`host-demo/README.md`); on the blocked variant it aborted
and the guard denied the host's own submission. 72 further runs across
skill forms and prompts complied in every case (`skill-forms/`). The
demo found and fixed a real ledger defect (typed step names did not
match their rules). Not shown: OS-level isolation in that setup.

**Which guarantees are statically checked, runtime-enforced, or
agent-dependent?**

| Guarantee | Where |
|---|---|
| Procedure parses; order/authority/effect rules hold | `check` (static) |
| Only verified bytes reach a protected target; single-use approvals; fail-closed crashes | guard (runtime, needs host isolation) |
| Observation happened in a networkless container | `sandbox` / `ledger exec --readonly` (runtime, needs docker) |
| Log matches independent checkpoint; attempts satisfy nothing | audit / ledger (runtime) |
| The check actually ran; the candidate is the real output; verify steps without guard ops | agent cooperation (recorded, not enforced) |
| Thoroughness, correct scoping, no invented findings | reviewer discipline (assisted, not replaced) |

**What manual steps prevent ordinary developers from adopting this?**
Hand-authoring flows needs DSL knowledge (no syntax help beyond
`check` errors); guard policies must be hand-built with pinned
digests; approval is a manual ceremony; cross-skill runs need the target file
present at check time. Inline JSON arguments are no longer needed:
adapters follow `--` as plain words (0.9).

## Unknowns (not assessed)

- Behaviour on a harder task or a weaker host: every real-agent run
  complied, so the forms comparison hit a ceiling [U].
- Human (not model) review of the corpus and of the model drafts [U].
- OS-isolated host integration (guard under a separate account with a
  real agent) [U]; isolation itself is tested by `isolation_probe.py`.

## 0.9.0 blockers: status 2026-11-17

- P0 real-host invocation demo: done (`host-demo/`).
- P0 required status checks on `main`: done 2026-11-12.
- P1 model draft + fidelity measurement: done (`nl-fidelity/model-draft/`).
- P1 independent corpus review: done by a fresh model session, not a
  human (`nl-fidelity/independent-review/`); four reference-flow defects
  recorded for a re-frozen v2.
- P1 Windows quoting: adapters accept plain argv after `--` (`draft`,
  `benchmark_runtime.py`); `--adapter-file` kept.
- P2 typed terminal steps and declared read-only exec: done (SPEC
  Section 21).

## Next gate (0.10)

- Corpus v2: fix the four reference defects, re-freeze, rerun drafts.
- Drafter evidence lint: fail or warn when a gate loses its `exec`
  evidence (the main silent-loss class).
- A task hard enough to separate skill forms, and an OS-isolated host run.
