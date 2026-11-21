# Live skill build with the plugin (2026-11-20)

Does the packaged `skillwren` plugin let a real agent build a new, checked
skill from a one-line request? One task, one model (`sonnet`, headless
Claude Code), two runs, author-scored. It shows the path works, not a rate.

**Setup** (`harness.py`): an empty temp project holding only a starter
`CHANGELOG.md`; `claude -p --plugin-dir plugin` with no user settings and no
MCP servers; tools limited to Read/Write/Edit/Glob/Grep/Skill and
`py`/`python` commands. Two turns in one session:

1. "Use skillwren to build a new skill named changelog-entry ..." (read the
   changelog first, ask Added or Fixed when unclear, never edit another
   file, show the entry before writing).
2. Resumed: "Confirmed: the inventory is complete and correct. Go ahead."

## Results

| | Run 1 | Run 2 (`--add-dir plugin`) |
|---|---|---|
| Turn 1 | 10-line inventory (5 marked inferred), asked to confirm, **wrote nothing** | same behavior, wrote nothing |
| Turn 2 | wrote the draft; the checker command hit a permission prompt the harness could not answer; the agent stopped and said the skill was not built | draft, check, repairs, explanation, `build` to `./changelog-entry` |
| Result | draft: 0 errors, 3 warnings (W15, W9, W5), unrepaired | built skill: **clean, 0 warnings**; byte-identical to the checked draft |
| Cost | $0.16 | $0.25 |

Independent re-check of run 2's output (`run2/built-SKILL.md`): one flow,
gates `1 evidence, 1 self, 2 user`, three order rules resting on evidence
or a user decision (`verify #changelog before generate entry`, `verify
#changelog before ask user to choose`, `ask user to approve the entry
before write entry`). The project's own `CHANGELOG.md` was untouched; the
agent told the user to run `approve` themselves and did not run it.

## What this shows and does not

- The skill's confirmation point works headless: dismissal-safe, nothing
  written before the inventory is confirmed.
- The check loop does its job: run 1's unrepaired draft had three warnings;
  run 2's repaired one has none.
- Run 1 is a harness finding: a plugin's launcher lives outside the
  project, so a host that restricts commands to the project needs the
  plugin directory allowed (`--add-dir`), or the user approves the prompt.
- Not shown: that the built skill, when used, makes a model follow it;
  other models; other tasks.

## Scenario matrix (0.12.1, 2026-11-20)

Harness: `scripts/lab/skill_build_live.py` (committed). Four scenarios, two
models, one session each: an inventory **correction** (the user rejects
part of the inventory, then confirms), two new skills of different shapes
(`release-gate`: tests, version decision, tag, never push;
`issue-triage`: classify, ask when unclear, write a file, never touch the
issue), and a **conversion** of the prose `code-reviewer` skill
(read-only tools, so its logic must contain no `write`). Scored
mechanically; checks run on the folder `build` wrote, in that skill's
own mode.

**Matrix A** (`matrix-a/`, $1.29, before the destination fix). The
first scorer checked the wrong folder in one mode; `rescore.jsonl` is the
corrected score. During this matrix the plugin folder held the
pre-budget skill for about two seconds (a test of the new loop check);
the scored behavior is the same in both versions.

| Scenario | Sonnet | Haiku |
|---|---|---|
| correction: nothing written before confirm; revised inventory shown | yes | yes |
| correction: built, corrections present | 0 errors, 1 W15 (explained) | 0 errors (complete-skill form) |
| release-gate | 0 errors, 0 warnings, order rule present | 0 / 0, order rule present |
| issue-triage | 0 / 0 | 0 / 0 |
| convert code-reviewer | 0 / 0, no `write` | 0 errors, 6 W15 (explained), no `write` |
| package at the requested path | 4/4 | **0/4** (`-pkg`/`-build` siblings) |

Every run wrote nothing before confirmation and left the project's files
untouched. Finding: Haiku drafted into the requested folder or passed a
file to `build`, then had to put the package beside it. Fixed in 0.12.1:
the draft is always `<name>-draft/`, the requested path is the build
destination only, and `build` takes the draft folder.

**Matrix B, Haiku after the fix** (`matrix-b-haiku/`, $0.09): package at
the requested path in 3/3 builds. `release-gate` did not build, correctly:
the confirmed order ("run tests, then ask for the version") puts a
possibly-writing command before a dismissible question (M1), Haiku would
not mislabel the test run `exec readonly`, and it stopped with the draft,
the conflict and three options, the blocked exit added in 0.12.1. Sonnet
resolved the same scenario in matrix A.

Limits: one run per cell, author-scored, synthetic tasks; corrections were
scripted, not a real user; no human review of the built skills' fidelity
to intent beyond the expected-phrase and no-write checks.

## Corrections to the 0.12.1 figures (2026-11-20)

- "11 of 12 built" combined matrix A (pre-fix) with matrix B (Haiku after
  the destination fix); it was never one frozen configuration.
- Matrix A's clean Sonnet `release-gate` build marked the test run
  `exec readonly` (`matrix-a/release-gate-sonnet/files/release-gate/SKILL.md`
  line 23). That silences M1 by weakening what the skill claims: tests can
  write caches and artifacts. It should not have counted as a success.
- The pre-confirmation score checked only for new paths, not edits or
  deletions of existing files.

## 0.12.2: frozen configuration (`matrix-d-0.12.2/`, $1.46)

Changes under test: the skill forbids relabeling a possibly-writing command
`readonly` to satisfy M1; the launcher counts repairs (below); the harness
snapshots every file byte for byte after each turn and captures every tool
call. One frozen plugin (`plugin/skillwren/SKILL.md` unchanged during the
run), five scenarios, two models, one run per cell. A fifth scenario,
`unfixable-order`, asks for "delete with make clean, then ask whether to
rebuild" with the order fixed and the command not read-only: M1 cannot be
satisfied without breaking a confirmed requirement.

| Scenario | Sonnet | Haiku |
|---|---|---|
| correction, then confirm | built, 0 errors, 0 warnings; 3 repairs | built, 0 / 0; 1 repair |
| release-gate | stopped (M1 vs confirmed order; no relabel) | stopped (same) |
| issue-triage | built, 0 / 0; 1 repair | built, 0 / 0; 2 repairs |
| unfixable-order | stopped, 1 repair, no relabel | stopped, 1 repair, no relabel |
| convert code-reviewer | built, 0 errors, 5 W15 (explained), no `write`; 1 repair | built, 0 errors, 6 W15 (explained), no `write`; 4 repairs |

- Nothing created, modified or deleted before confirmation: 10/10.
- Project files untouched at the end: 10/10.
- Built with 0 errors: 6/6 of the scenarios that can be satisfied honestly;
  stopped blocked: 4/4 of those that cannot; `exec readonly` in any draft
  or build: 0/10.
- Repairs per run (the launcher's own record): 0-4, within the budget of
  five in 10/10.

**Why the budget moved into the launcher.** Matrix C (`matrix-c-0.12.2-model-budget/`,
the same scenarios with the budget left to the model's own count) built and
stopped the same way, but its session transcripts show one Haiku run making
about eight edit-and-check rounds before reaching a clean check, past the
five the skill allowed; nothing stopped it. In 0.12.2 the launcher records
each check of a `*-draft` folder (`.skillwren/budget.json`, skipped by
`build`) and exits 3 with a reason after five repairs without a clean
check, or as soon as a repair leaves exactly the same result. Unit tests
cover the five-repair stop, the no-progress stop, a clean draft never
stopping, non-draft folders left untouched, and the record never being
packaged. The model can still delete the record; the skill tells it not to.

Limits: one run per cell; synthetic tasks; scripted corrections; the
expected-phrase, no-`write` and no-relabel checks are smoke tests, not a
measure of whether a built skill means what its source meant (that needs
reviewed requirements; since run as the fidelity benchmark against an
AI-reviewed baseline, `../fidelity-benchmark/`).

## 0.13.0 smoke: coverage in the skill (`smoke-0.13.0-coverage/`, $0.03)

One run (Haiku, `issue-triage`) on the frozen 0.13.0 plugin: built at the
requested path with 0 errors, 2 repairs, nothing changed before
confirmation. The agent ran `coverage` and reported "0 enforced, 0
recorded, 4 instructed. Nothing outside the model blocks or records the
label gate, the issue-text check, or the `triage.md` write." The 0.12.2
matrix above was not rerun for this one added step.
