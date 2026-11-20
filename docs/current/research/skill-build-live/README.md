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
