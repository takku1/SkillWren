---
name: skillwren
description: Check SkillWren procedures and ordering rules, convert existing skills to checked logic, or record command evidence with the SkillWren ledger.
---

# SkillWren in this checkout

Resolve the repository root three directories above this skill directory.
Use its `scripts/skillwren.py` launcher with Python 3.9+ (`py -3` on Windows,
`python3` on macOS/Linux). It needs no package installation. Use an absolute
launcher path when working in another directory; target paths resolve from
that working directory. Pass explicit filenames rather than shell globs on
Windows.

For ordinary Markdown flow files, run `check --fragment --summary --audit
<file>`. For complete SkillWren contract-header skills, run `check <file>`.
Exit 0 means no errors, 1 means validation errors, and 2 means usage failure.
Warnings still require interpretation. Do not validate a plain Codex skill
as a complete SkillWren skill just because it is named SKILL.md.

For conversion, read [the conversion procedure](../../../skills/skillwren/SKILL.md)
using the linked path from this directory.
Resolve its `docs/current/` references from the repository root. Preserve
source behavior and authority; passing validation does not prove parity.

For runtime evidence, use `ledger start <flow-file>` and retain the printed
run ID. Use `ledger exec <id> --step "<named step>" -- <command> <args>` for
command evidence, `ledger note` for self-reports or artifact hashes, then
`ledger check <id> --require-evidence`. Failed commands do not establish a
prerequisite. Record only actions actually performed. The ledger is an
offline trace check, not enforcement or proof of omitted actions.

`conform` is Claude-only; do not present it as a Codex evaluation. Static
checks, builds, measurements, and ledger operations do not require Claude.

