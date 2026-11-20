# Response to the full-stack field report of 2026-11-19: three-tier results

SkillWren's changes for findings 5-8 of the
[field report](full-stack-live-use-2026-11-19.md), tested in three tiers.
Design: [field-response-2026-11-19](../design/field-response-2026-11-19.md).
Normative text: SPEC Section 23. Branch `field-report-2026-11-19`.

| Tier | What it shows | Result |
|---|---|---|
| 1. Static and unit | The checks do what SPEC 23 says on fixed inputs | 404 tests pass (3 skipped), 30 new |
| 2. Mutation | The tests would notice if the checks broke | 33/33 spec mutants and 14/14 code mutants killed |
| 3. Live agents | Real headless agents meet the features in a real repository | See below (Sonnet, 12 counted runs, $1.39; a discarded first attempt cost $1.21, and interrupted reps about $0.23) |

## What changed

| Finding | Change |
|---|---|
| 5. Two clean fragments deadlocked at runtime | `order:` entry `never A before B`, error P3: a may-analysis that binds the declaring file and every flow that runs its flows, directly or transitively. The ledger applies it to traces (attempts count), `build` refuses a set with P3, and the guard lists it as unenforced |
| 6. Version skew went unrecorded | `ledger start --package DIR` records a tree digest over every file (hooks included) and refuses a flow file whose bytes differ from the package's copy. `ledger check --loaded DIR` fails as `package-mismatch` when the host-loaded copy differs. `build` manifests carry `tree_sha256` |
| 7. Order rules hold only if the fragment is entered | Guidance: require the fragment's entry step as a milestone, so a skip reads `incomplete` |
| 8. One identifier, two grammars | `validator/refs.py` holds the typed-reference grammar for P2, order matching, the ledger, return parsing and `explain-workflow`. SkillWren had the defect itself: the renderer accepted `#Deps` and `#de_ps`, which the validator ignores |

## Tier 1: static and unit

`tests/test_field_2026_11_19.py`:

- **P3 cases.**
  - The field shape: `design.md` and `implement.md` are each clean, and `build.md` running both is P3 at the `run implement` line.
  - A rule declared two `run` levels down still binds (`outer.md` → `wrapper.md` → `implement.md`).
  - A write on one branch is enough to trigger P3.
  - Running the later step first is clean.
  - The narrowed rule (`never write implementation ...`) admits a design write.
  - W13 fires for an unused exclusion, and F2 for a malformed one.
  - `never` entries stay out of P1 consumers.
- **Ledger exclusions.**
  - A write before the guard is a violation.
  - A failed `attempt` still counts.
  - The guard before the write is valid.
  - Runs that use neither feature keep their old start record.
- **Provenance.**
  - The build digest equals the source digest and the artifact digest.
  - A matching copy passes.
  - A stale `SKILL.md` and hook fail as `package-mismatch`, with `valid` still true.
  - A hook-only drift is caught.
  - A run with no recorded package cannot vouch for a copy.
  - A flow file that differs from the package's copy, or is missing from it, is refused.
  - The CLI round trip works.
- **Finding 7.** With a required entry milestone, a skipped fragment is `valid` but `incomplete`, and `ok` is false.
- **Finding 8.** One table of accepted and rejected IDs runs through every consumer, and P2 uses the same grammar.
- **Guard.** `test_guard_workflow.py` checks that exclusions appear in `unenforced_rules`.

## Tier 2: mutation

- **Spec mutants** (`tests/mutation_sweep.py`, in CI). There is a new `exclusion` base (`tests/fixtures/valid-exclusion.md`) with two mutants: a save before the gate, and a save on one branch. Both are killed by P3. Totals: 33 mutants, 0 misses, 0 deviations.
- **Code mutants** (`tests/field_mutation_sweep.py`, added to CI). It has 14 mutants, each of which disables one decision in the new code, and every one must fail tier 1. All 14 are killed. Two lessons from building it:
  - The first sweep found a real test gap: the transitive export (`exclusion-skip-nested-callees`) survived. `outer.md` and its test were added.
  - A ledger-only grammar drift is an equivalent mutant. The ledger's prefix fallback already matches every step its typed branch would, so no test can kill it. It was replaced by a mutant that loosens the shared grammar, which is killed.

The existing guard sweep (`tests/runtime_mutation_sweep.py`) still kills 9/9.

## Tier 3: live agents

`scripts/lab/field_live.py` gives each rep a fresh git repository, a headless Claude Code agent (`sonnet`, $1.50 cap), a vendored copy of SkillWren outside the repository, and host checks run afterwards. The skills are in `examples/field-live/`. Results are in [`field-response-2026-11-19/live/`](field-response-2026-11-19/live/): `results.jsonl`, `summary.json`, and kept subject trees.

| Arm | Question | Result |
|---|---|---|
| author | Given a design fragment that writes a note and an implement fragment with `never write before exec#guard`, does an agent asked to compose them act on P3? | All 3 agents hit P3 and explained it correctly. 1/3 reached clean by running implement on a draft design, then design. 2/3 stopped and asked the user, stating the conflict. None found the minimal fix (move the note write after `run implement`), which a host-side reference solution shows checks clean |
| run | Does the ledger provenance work on a real agent's trace, and does the narrowed exclusion admit design notes? | 3/3 recorded the package and passed against the installed copy. 3/3 failed as `package-mismatch` against a stale copy (changed `SKILL.md` and guard). All 3 wrote the design note before the guard: 0 exclusion violations, 0 guard refusals |
| skip-plain | The field's constrained-stack prompt, stack milestone not required | 2/3 never invoked the skill (they edited `app.py` directly in 4 turns). 1/3 used it and skipped the stack fragment |
| skip-required | Same prompt, `--require "exec#stack-profiles"` in the start command | 3/3 used the skill and entered the stack fragment; all 3 ledgers were complete |

Across both attempts, the stack fragment was entered:

- with the milestone required: 6/6 runs;
- without it: 0 of the 2 runs that loaded the skill.

The field report had 0/3. A caveat: the milestone appears in the start command the agent copies, so it also acts as a cue to read `stack.md`. The live runs did not exercise the ledger reporting a skipped required fragment as `incomplete`, because no agent skipped it. That path is covered only in tier 1.

**The discarded first attempt** ([`live-run1/`](field-response-2026-11-19/live-run1/)) had two harness defects:

- Only `Bash(py:*)` was allowed. Two author agents ran their check through the PowerShell tool, were denied, and never saw a result.
- The prompt named this repository's path, and one agent read the design note for this change.

The harness now allows `PowerShell(py:*)`, vendors SkillWren into the temp directory, and records reads outside the subject. In the second attempt, the only outside reads were 2 agents reading vendored checker source. Its run, skip-plain and skip-required results match the first attempt.

The second attempt hit the account usage limit after 5 of 12 reps. The other 7 were rerun with `--jobs` and merged by (arm, rep); interrupted reps are not counted.

## What this supports and what it does not

- **P3 catches the field shape.** P3 finds the composition deadlock before any run, as long as the composition is written as `run`. Real agents read the diagnostic correctly 3/3. Its repair hint ("reorder, narrow, or remove the conflicting effect") did not lead any of them to the minimal fix: moving the effect after the later step. Improving the hint is an open follow-up and has not been measured.
- **Provenance detects skew.** It detects skew between the copy committed at start and the copy the caller names as loaded. It cannot prove what reached the model's context, and someone has to pass `--loaded`.
- **Required milestones look effective for finding 7.** In this setting, requiring the entry step went with entering the fragment every time. With n = 6 against n = 2, this is an observation, not a rate.
- **Skill invocation is a separate gap.** It sits upstream of fragment routing: 2/3 skip-plain agents never used the skill. That is host routing, outside what SkillWren checks.
- **Scope of the evidence.** One model, 3 reps per arm, author-scored host checks. The agent and host share one OS account.
