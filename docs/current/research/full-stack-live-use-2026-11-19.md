# Full-stack live use of SkillWren 0.9 (2026-11-19)

Second report from SkillWren's maintained consumer, after [the 2026-11-12 report](full-stack-live-use-2026-11-12.md). Full-stack moved from SkillWren 0.6-0.7 to 0.9 (full-stack packages 0.8.1 to 0.8.3, decision D-024), ran its first full pressure evaluation (18 headless sessions), and built a kernel slice in a large live repository (MochiOS) under the run guard. Sources in full-stack: `docs/design-decisions.md` D-024, `evals/results/pressure-2026-11-19.md`, `docs/research/field-report-2026-11-19-mochios-4.md`. Evidence is one consumer, two models (`sonnet` headless for the pressure run, Opus 5.5 interactive for the build), author-scored. It shows how SkillWren behaves in use, not rates.

## Summary

| # | Kind | Finding | Status |
|---|---|---|---|
| 1 | Adoption | Typed return anchors (SPEC 21) adopted through SkillWren's PR full-stack#1: `verify#table before return#assurance`, `verify#consistency before return#records`. The new mutant (check run, verdict ignored) passed the old rule with only W5 and now fails P1 | Merged; full-stack flow checks now require 0.9 |
| 2 | Adoption | `skillwren build skill/full-stack` packages the fragment set cleanly (4 fragments, 40 files, 0 warnings); the 0.7 ledger API works unchanged on 0.9 | Verified, not used for distribution (Claude Code plugin instead) |
| 3 | Not adopted | `exec readonly`, `approve`, the recommended inline `SKILL.md` form. Reasons below | Consumer decision |
| 4 | Ledger | 18 pressure sessions plus 2 guarded build runs: every run that closed reported `valid, complete`; none was blocked by the ledger | Answers the 2026-11-12 open question for these scenarios |
| 5 | Static vs runtime | All four flows check clean, yet two flows together created a runtime deadlock: one fragment's `write` made another fragment's runtime precondition unsatisfiable | Fixed in full-stack's guard; suggestion for SkillWren |
| 6 | Version skew | The host ran a cached 0.8.0 skill and hook while the repository's 0.8.2 scripts wrote the ledger. The ledger records the flow's digest but not which package enforced the run | Suggestion |
| 7 | Routing | Order rules inside the stack fragment were never exercised: the model judged the fragment's entry condition false in 3/3 sessions | Evidence on the limits of static order guarantees |
| 8 | Shared grammar | A checker and a runtime matcher disagreed on an identifier grammar (`[A-Z]+-n` vs `A-n`), the same class as SkillWren 0.9's typed-reference ledger fix | Fixed in full-stack; pattern note |

## 1-3. Adoption status

| SkillWren feature | Full-stack use | Why |
|---|---|---|
| Fragments, `order:`, cross-file `run` (0.6) | Used, all four flows | D-023 |
| Run ledger (0.7) | Written by the run guard, checked at `close` | D-023 |
| Typed returns (0.9) | Used in `assurance` and `stack`. `implement` keeps statement-text rules because the guard names ledger steps after them | D-024 |
| `exec readonly` (0.9) | Not used | The marker is a claim M1 then skips, enforced only by `ledger exec --readonly` in a sandbox full-stack does not run. The costly-commitment `ask` already precedes every `exec`, so it would buy nothing |
| `approve` (0.8) | Not used | Binds a human to exact flow bytes; it is the owner's act, and every flow edit would invalidate it |
| Inline form in `SKILL.md` (0.9 recommendation) | Not used | It would load every flow on every run, against full-stack's ~720-token core (FS-009 evidence). The 72-run result shows agents follow whichever single form is present, not that inline beats on-demand fragments |
| `build DIR` (0.9) | Verified only | Distribution is the plugin |

## 4. Ledger in use

The pressure run: 3 scenarios x skill/control arm x 3 reps, `sonnet`, $4.23. Every skill session that closed its guarded run printed `SkillWren ledger (flows/implement.md order rules): valid, complete`. One session never closed (the guard correctly refused an unverified run, and the model stopped and asked). The MochiOS build closed `valid, complete` with 11 checks over host tests and two native boots. A second guarded run, editing full-stack itself, also closed `valid, complete`.

## 5. Each flow checks clean, but two of them deadlocked at runtime

`design.md` ends with `write design with design_docs` (the note holding the assurance table). `implement.md` has `exec guard start before write implementation`, and the guard refuses to start over uncommitted edits it did not see, unless the user adopts them. Each fragment is clean. Run in the order a build follows (design, then implement), the design's own `write` became a foreign edit at `start`. The obvious repair, starting first, hit a second runtime rule (the hook blocked all edits until declaration), so neither order worked. It reproduced in a clean scratch repository and in a live session, where the permission layer also refused the agent's attempt to adopt its own note.

The checker could not see this. The conflict sits between a `write` effect in one fragment and a runtime precondition attached to an `exec` in another, across a routing boundary (the core picks design, then implement, in prose). Full-stack fixed it on its side: notes stay writable until declaration, and only code changes make a declaration late. Possible SkillWren angles, offered without a design:

- Let an `exec` declare a precondition over earlier effects, such as "no unseen `write` to the write set", so cross-file `run` analysis can flag an earlier `write` that would violate it.
- Or treat "a later step's runtime gate refuses an earlier step's effect" as a mutant class, so a test can pin it.

## 6. Version skew between what the agent read and what enforced the run

Claude Code loaded the plugin from its cache at 0.8.0 (installed 2026-11-13), so the agent read 0.8.0's `SKILL.md`, and the 0.8.0 hook guarded edits. The scripts run by path came from the repository at 0.8.2, and they wrote the ledger. The ledger's `start` record names `implement.md` with its `file_sha256`, which is the repository's file. So the ledger was internally consistent, and `valid, complete` was true of the rules it committed to. Nothing records that the instructions in the agent's context and the hook enforcing them were different bytes. Suggestion: let `ledger start` take the enforcing package's manifest digest (the `build` manifest would serve), and let `ledger check` or `approve --check` report a mismatch with the host-loaded copy when the caller supplies it.

## 7. Static order guarantees are conditional on entering the fragment

The `constrained-stack` pressure scenario ("Python standard library only") went 0/3 on the stack step in the skill arm. All three sessions read `flows/stack.md`. None ran its `exec stack profiles` or `exec stack check`, because `design.md`'s `if any layer needs a technology chosen or reopened` was judged false. One session wrote "every layer is therefore fixed, no stack flow", then chose between two standard-library stores. Different sessions chose differently (SQLite twice, a JSON file once). The stack fragment's P1 rules held vacuously. This matches SkillWren 0.9's decision that judgment conditions stay unrecognized and should be nested or given an explicit verifier. Here no verifier exists, because whether a choice exists is itself the judgment. Field rate: 0/3. Full-stack has not decided on a runtime gate for it.

## 8. One identifier grammar, two implementations

Full-stack's table checker accepted row IDs `[A-Z]+-n`, while the guard matched only `A-n` in check criteria. A table passed its check, and then close could never match its rows. This cost a pressure session a whole extra run. SkillWren 0.9 fixed the same class of defect: typed-reference step names did not match ledger rules, so the documented pattern was silently unexercised. Pattern worth stating in the authoring guide: when a static check and a runtime matcher share an identifier, define the grammar once and test both against it.

## Limits

One consumer, author-scored. Pressure rates are 3 sessions per cell. The build is one session in one repository. Full-stack changed its guard during this report, so items 5 and 8 describe before-and-after in one package. Nothing here was changed in SkillWren; its maintainers adopt or decline.
