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
| skip-plain | The field's constrained-stack prompt, stack milestone not required | **Confounded; superseded by the 2026-11-20 follow-up below.** 2/3 never invoked the skill. 1/3 used it and skipped the stack fragment |
| skip-required | Same prompt, `--require "exec#stack-profiles"` in the start command | **Confounded; superseded below.** 3/3 used the skill and entered the stack fragment |

**Correction (2026-11-20).** Each rep's temporary directory was named after its arm (`sw-live-skip-plain-…`, `sw-live-skip-required-…`), and the agent sees its working directory. With identical skill listings (confirmed by asking the host), skip-required loaded the skill 10/10 and skip-plain 1/10 across this attempt and a probe. With a neutral prefix, 2 of 18 skip agents loaded the skill. The skip rows above and the "6/6 against 0 of 2" claim measured the path cue, not the milestone. The author and run arms are unaffected: their directory names carried no cue about the task.

**The discarded first attempt** ([`live-run1/`](field-response-2026-11-19/live-run1/)) had two harness defects:

- Only `Bash(py:*)` was allowed. Two author agents ran their check through the PowerShell tool, were denied, and never saw a result.
- The prompt named this repository's path, and one agent read the design note for this change.

The harness now allows `PowerShell(py:*)`, vendors SkillWren into the temp directory, and records reads outside the subject. In the second attempt, the only outside reads were 2 agents reading vendored checker source. Its run, skip-plain and skip-required results match the first attempt.

The second attempt hit the account usage limit after 5 of 12 reps. The other 7 were rerun with `--jobs` and merged by (arm, rep); interrupted reps are not counted.

## What this supports and what it does not

- **P3 catches the field shape.** P3 finds the composition deadlock before any run, as long as the composition is written as `run`. Real agents read the diagnostic correctly 3/3. Its repair hint ("reorder, narrow, or remove the conflicting effect") did not lead any of them to the minimal fix: moving the effect after the later step. Improving the hint is an open follow-up and has not been measured.
- **Provenance detects skew.** It detects skew between the copy committed at start and the copy the caller names as loaded. It cannot prove what reached the model's context, and someone has to pass `--loaded`.
- **Required milestones work for finding 7, with a caveat (see the follow-up).** Once the skill is loaded, an unrequired stack step was entered 0/6; required, 6/6; required but hidden from the agent, skipped 6/6 and recovered 6/6 after `ledger check` named the missing milestone. The recovery came after the code was written.
- **Skill invocation is a separate gap.** It sits upstream of fragment routing: with neutral paths, 16 of 18 agents given the field's prompt never loaded the skill. That is host routing, outside what SkillWren checks.
- **Scope of the evidence.** One model, 3 reps per arm, author-scored host checks. The agent and host share one OS account.

## Follow-up (2026-11-20)

Work on the open items from the first pass. Live runs are Sonnet, $1.50 cap
per rep, harness `scripts/lab/field_live.py` with a neutral temporary
directory prefix.

**P3 repair hint.** The hint now names the earliest statement with a path
to the later step and, when that statement is a `run`, the effect inside
the callee: "'run design …' (line 5) reaches 'write design with
design_docs' (design.md line 9). Take that step out of the called flow and
do it after 'run implement …' (line 7)…". Author arm rerun
([`live-hint/`](field-response-2026-11-19/live-hint/), 3 reps, $0.43):
2/3 applied exactly that fix (moved the note write out of `design.md` and
after `run implement`) and checked clean. The third saw P3, then had its
later checker calls denied because it prefixed them with `cd`/`Set-Location`
(the harness allows only commands starting with `py`); it never reached a
fix. Against 0/3 with the old hint.

**W16, prose composition.** A file that names, outside a `run` line,
another file declaring exclusion rules, without reaching it by `run`,
warns W16. Over the repository's examples and fixtures it fires once:
`examples/field-live/build-notes/SKILL.md`, the router that sends the
agent from design to implement in prose, which is the field's shape.

**Host-load records.** `skillwren ledger record-load`, a Claude Code
`PostToolUse` hook on `Skill`, records which copy of a skill the host
loaded and its digest at load time; `ledger check` uses it when no
`--loaded` is given. A probe showed the hook event carries only the skill
name (`{"skill": "demo"}`), so the copy is resolved in the host's
documented order and the record is marked `ambiguous` when installed
copies differ. Real-host check: a Haiku session in a temporary project ran
the hook, the record matched the skill's digest, and after the skill was
edited a fresh run's `ledger check` (no flag) failed as `package-mismatch`.

**Guard enforcement of exclusions.** Under a workflow-bound guard, a
`never A before B` rule whose two steps are policy operations is enforced:
once A has run, B is denied with the rule named. Other exclusions stay in
`unenforced_rules`.

**Finding 7, rerun without the path cue**
([`live-skip-invoked/`](field-response-2026-11-19/live-skip-invoked/),
18 reps, $1.87). The prompt names the skill (`--invoke`), so every agent
loads it and the measurement starts after host routing. A new arm,
skip-hidden, puts the requirement in a host wrapper (`start_run.py`), so
the start command the agent copies does not mention the stack step; no
agent read the wrapper.

| Arm | Loaded skill | Ran the stack step | How |
|---|---|---|---|
| skip-plain | 6/6 | 0/6 | Reproduces the field's skip; ledger `complete` because nothing required it |
| skip-required | 6/6 | 6/6 | Before writing code |
| skip-hidden | 6/6 | 6/6 | Skipped it 6/6; the closing `ledger check` listed the missing milestone 6/6; all 6 went back and ran it, after the code was written |

What this supports: a required entry milestone turns a silent skip into
an `incomplete` run, and in this setting agents acted on that 6/6. What it
does not: completeness says the milestone happened, not that it came
first; to make a late recovery a violation, add the order rule
`exec#stack-profiles before write#code`. No agent in any arm read
`stack.md`; each ran the milestone command from the skill's table, so
"ran the stack step" is not "followed the stack fragment".

Superseded evidence is kept and labelled:
[`live-skip/`](field-response-2026-11-19/live-skip/) (path-cued, 18
reps, $1.53), [`live-skip-probe/`](field-response-2026-11-19/live-skip-probe/)
(tool sequences that located the cue, 8 reps, about $0.75), and
[`live-skip-neutral/`](field-response-2026-11-19/live-skip-neutral/)
(neutral paths, prompt without the skill name: 2/18 loaded it, 18 reps,
$1.34).

**Tests.** 417 pass (3 skipped); spec sweep 33/33; code sweep 20/20 (new
mutants for the hint, W16, guard exclusions, a failed check counting as
run, the host-load fallback, and personal-before-project resolution);
guard runtime sweep 9/9.

## Second model: Haiku (2026-11-20)

Same harness, `--model haiku`, 3 reps per arm.

**Author arm.** Without a prompt note, all 3 agents prefixed their check
commands with `Set-Location`/`cd`, which the `py`-only allowlist denies, so
none saw a check result ([`live-haiku-author/`](field-response-2026-11-19/live-haiku-author/),
unscored). With `--cwd-note` (the prompt adds "run each command exactly as
given, with no `cd`"; a prompt change, so not pooled with Sonnet)
([`live-haiku-author-cwd/`](field-response-2026-11-19/live-haiku-author-cwd/)):
3/3 saw P3 with the new hint. 1/3 reached clean by writing the note after
`run implement`, as the hint says, but copied the design steps inline
instead of running `design.md`, so the host check (runs the design flow)
fails. 2/3 stopped and reported the error. Haiku reads P3 but rarely
completes the repair; Sonnet applied the named fix 2 of the 2 times it
could keep checking.

**Finding 7, skill invoked** ([`live-haiku-skip/`](field-response-2026-11-19/live-haiku-skip/)):

| Arm | Ran the stack step |
|---|---|
| skip-plain | 1/3 |
| skip-required | 3/3, before code |
| skip-hidden | 3/3: 2 before code unprompted, 1 after `ledger check` named the missing milestone |

Haiku entered the stack step more readily than Sonnet without a
requirement (1/3 against 0/6). The direction matches Sonnet: a required
milestone, visible or not, ends with the step run. Package provenance
held on Haiku too: 9/9 runs recorded the package and 9/9 stale copies were
caught. Haiku cost $0.18 for all 15 counted and uncounted runs.
