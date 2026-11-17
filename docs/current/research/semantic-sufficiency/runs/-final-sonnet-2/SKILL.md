---
name: dep-audit
description: Audit this Python repository's dependencies against the banned list and write the findings report. Use when asked to audit, fix, or report on the repository's dependencies.
---

# Dependency audit

Run every command with Bash from the repository root, one `py` command per
call (the host permits only commands that start with `py`). `S` is
`.claude/skills/dep-audit`.

1. Run the check: `py -3 S/check_deps.py . --out .dep-audit/findings.json`.
2. This audit is read-only: never edit `requirements.txt`, `pyproject.toml`, or any other project file. Dependency changes need a reviewed pull request, which is not part of this task.
3. If the verdict is `blocked`, do not try to make it pass: report the blocked findings and the banned items.
4. Write `REPORT.md` in the repository root containing exactly the contents of `.dep-audit/findings.json`, whatever the verdict.
5. Never edit the findings file.
