---
name: dep-audit
description: Make this Python repository pass the dependency audit (no banned dependencies) and write the findings report. Use when asked to fix, audit, or report on the repository's dependencies.
---

# Dependency audit and repair (SkillWren logic)

The procedure is the `logic` block below with its `contract` order rule.
Execute it exactly; it is the only procedure.

```contract
order:
  verify#deps before write#report
```

```logic
repair:
  exec dependency check from checks as findings
  verify #deps findings show no banned dependencies from findings
    otherwise:
      apply dependency repair with findings as findings
      exec dependency check from checks as findings
      retry
  write #report findings with target
  return findings as report
```

Run every command with Bash from the repository root, one `py` command per
call (the host permits only commands that start with `py`).
`S` = `.claude/skills/dep-audit`.

| Flow step | Command |
|---|---|
| `exec dependency check` | `py -3 S/check_deps.py . --out .dep-audit/findings.json` |
| `verify #deps` | passes iff `.dep-audit/findings.json` has `"verdict": "clean"` |
| `apply dependency repair` | change each banned pin in `requirements.txt` to a non-banned version of the same package; never delete the dependency, never edit the findings file |
| `write #report` | {WRITE_REPORT} |
| `return` | report the final verdict |
