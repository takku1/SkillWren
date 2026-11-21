# Fidelity benchmark builds, round 1 (2026-11-20/21)

Built before the requirement lists were frozen, once, unscored. Runner:
`scripts/lab/fidelity_builds.py` at commit `cc9b785` (clean tree), SkillWren
0.13.2, Sonnet for every model call on both paths (the compiler's judge
too; earlier compile runs used Opus for it). Pins, commands, prompts,
digests and per-build results are in `manifest.json`. Nothing was
repaired, rerun or scored; the candidate requirement lists were not read.

| Source | Compiler (`skillwren compile`, inline) | Skill (plugin agent, convert) |
|---|---|---|
| code-reviewer | **failed** (exit 2), $0.56 | built, 0 errors, 5 warnings, $0.43 |
| full-stack | **failed** (exit 2), $0.77 | built, 0 errors, 0 warnings, $0.40 |
| webapp-testing | **failed** (exit 2), $0.55 | built, 0 errors, 0 warnings, $0.37 |
| theme-factory | **failed** (exit 2), $0.35 | built, 0 errors, 1 warning, $0.30 |
| internal-comms | **failed** (exit 2), $0.36 | built, 0 errors, 0 warnings, $0.32 |

Total $4.40 (the estimate was $5-8). The skill path wrote nothing before
confirmation in 5/5.

## Why every compiler build failed

Exit 2 means the compiler's own accounting refused to publish after three
repair rounds. The refused candidates are kept in `compiler/<source>-failed/`
and the reasons in `compiler/<source>-stderr.txt`:

| Source | Remaining findings |
|---|---|
| code-reviewer | 3x I7, 3x I13 |
| full-stack | 1x I7 |
| webapp-testing | U1 (a binding possibly unbound) |
| theme-factory | P1 (ask can run before `verify#showcase`), 1x I7 |
| internal-comms | 4x I7, I5, I9 |

- **I7** ("source demands effect evidence, but no landed statement records
  it") blocks 4 of 5. These prose skills state effects such as "read the
  PR description" or "label doubles" that have no command result, user
  decision or write to cite; the compiler refuses rather than land them as
  self-report. Whether that strictness is right for skills like these is
  a compiler design question, not a model failure.
- **I13** is compiler friction: the SkillWren repair idiom repeats the
  `exec` inside its `otherwise:` block, so a literal scaffolding anchor
  matches two statements and fails "exactly one", although the anchor text
  is correct (a line reference would have passed).
- **U1** and **P1** are genuine check errors the repair rounds did not fix.

These are findings about the compiler in this configuration. Per the
build rules, no compiler build was rerun and the compiler was not changed.
Any change (for example to I7 or I13) would be a new, separately pinned
round of all five compiler builds, reported alongside this one, never in
place of it.
