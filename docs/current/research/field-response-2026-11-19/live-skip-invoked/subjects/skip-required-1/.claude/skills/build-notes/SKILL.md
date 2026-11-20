---
name: build-notes
description: Build a change in this repository - design it, then implement it under the run guard, choosing technology through the stack flow when needed. Use when asked to add, change or build a feature here.
---

# Build (SkillWren fragments)

Read `flows/design.md` and follow it. Then read `flows/implement.md` and
follow it. If any layer needs a technology chosen or reopened, read
`flows/stack.md` and follow it before implementing. Each flow's `logic`
block is the procedure; its `contract` order rules are checked on the
ledger at the end.

Run every command with Bash from the repository root, as its own call,
spelled out in full (the host permits only commands starting with `py`;
no shell variables, `&&`, `;`, or pipes). `S` = `.claude/skills/build-notes`,
`SW` = `py -3 C:/Users/dcarn/AppData/Local/Temp/sw-live-j2h2rn3u/tool/scripts/skillwren.py`. Edit files with Write or Edit.

Before any flow: `SW ledger start S/flows/implement.md --package S --label build --require "exec#guard" --require "write#code" --require "exec#stack-profiles"`
and remember the run id it prints.

| Flow step | Command |
|---|---|
| `write #notes` (design) | write the note with Write, then `SW ledger note <run> --step "write#notes" --artifact <note>` |
| `exec #stack-profiles` | `SW ledger exec <run> --step "exec#stack-profiles" -- py -3 S/stack_profiles.py` |
| `exec #guard` | `SW ledger exec <run> --step "exec#guard" -- py -3 S/guard.py` |
| `write #code` | edit the code with Write or Edit, then `SW ledger note <run> --step "write#code" --artifact <file>` (once per file) |
| finish | `SW ledger check <run>`. If it lists missing milestones, complete those steps and check again; report the last line |
