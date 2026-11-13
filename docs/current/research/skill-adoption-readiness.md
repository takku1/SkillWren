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
which the human had to replace. Requirement invention by a real model
is unmeasured; the fidelity corpus plus model-draft reproduction test
exists for exactly that measurement.

**Can a user understand exactly what the converted skill does?**
Largely: `explain-workflow` states steps, branches, order rules,
authority, effects, enforcement eligibility, and cross-file targets,
plus what it cannot show (prose meaning of untyped steps, correlated
conditions). Residual risk: terminal steps cannot be order-anchored
(no typed-ID form for returns), so pipeline order there rests on
written sequence.

**Can the packaged skill be invoked by a real coding agent against a
repository?** Not demonstrated. The three lifecycles were executed by
hand following the skill; packaging is a conventional `SKILL.md`
entry point, but no host integration test loads it. This is the
largest gap between the current evidence and the adoption claim.

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
digests; approval is a manual ceremony; inline JSON CLI arguments are
unusable from Windows shells (`--adapter-file` exists as a workaround,
added after hitting the C-runtime quoting trap); cross-skill runs need
the target file present at check time.

## Unknowns (not assessed)

- Whether a real host integration preserves the evidence chain (no
  host run yet) [U].
- Whether model-drafted flows reproduce approved requirements or
  silently add/drop them (corpus frozen, reproduction unrun) [U].
- Whether independent reviewers recover the same facts from
  explanations (protocol written, review pending) [U].
- Token/latency cost of the pipeline on real tasks [U].

## 0.9.0 blockers, prioritized

- P0: real-host invocation demo -- a packaged lifecycle skill loaded by
  an actual coding agent against a disposable repo, with ledger/guard
  evidence. Without this, "works with AI coding agents" is unproven.
- P0: required status checks on `main` (done 2026-11-12, all 14 lanes).
- P1: model draft + fidelity measurement (needs provider spend) and
  independent corpus review (needs a reviewer) -- both explicitly
  awaiting your approval, neither started.
- P1: Windows CLI quoting ergonomics beyond `--adapter-file`.
- P2: typed terminal steps for `order:` rules; static read-only exec
  syntax (runtime `--readonly` exists; the M1/static side needs a SPEC
  change, deliberately deferred).
