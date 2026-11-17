---
name: dep-audit
description: Audit this Python repository's dependencies against the banned list and write the findings report. Use when asked to audit, fix, or report on the repository's dependencies.
---

# Dependency audit

Bash from the repo root, one `py` command per call. `S` = `.claude/skills/dep-audit`.

- audit = run `py -3 S/check_deps.py . --out .dep-audit/findings.json` and report it
- audit != repair: project files stay unchanged
- blocked verdict = a valid result to report, != a problem to fix
- report = `REPORT.md` with exactly `.dep-audit/findings.json`, never edited findings
