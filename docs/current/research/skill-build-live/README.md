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
