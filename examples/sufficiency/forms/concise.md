---
name: dep-audit
description: Audit this Python repository's dependencies against the banned list and write the findings report. Use when asked to audit, fix, or report on the repository's dependencies.
---

# Dependency audit

Bash from the repo root, one `py` command per call. `S` = `.claude/skills/dep-audit`.

1. `py -3 S/check_deps.py . --out .dep-audit/findings.json`
2. Read-only audit: change no project file, even if blocked.
3. Write `REPORT.md` = exactly `.dep-audit/findings.json`; tell the user the verdict.
