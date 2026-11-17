---
name: dep-audit
description: Audit this Python repository's dependencies against the banned list and write the findings report. Use when asked to audit, fix, or report on the repository's dependencies.
---

# Dependency audit (SkillWren logic)

The procedure is the `logic` block below with its `contract`. Execute it
exactly. Bash from the repo root, one `py` command per call.
`S` = `.claude/skills/dep-audit`.

```contract
never:
  edit a project file
```

```logic
audit:
  exec dependency check from checks as findings
  write #report findings with report_file
  return findings as report
```

| Step | Command |
|---|---|
| `exec dependency check` | `py -3 S/check_deps.py . --out .dep-audit/findings.json` |
| `write #report` | write `REPORT.md` with exactly the contents of `.dep-audit/findings.json` (never edit the findings) |
| `return` | tell the user the verdict |
