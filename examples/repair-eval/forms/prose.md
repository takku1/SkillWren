---
name: dep-audit
description: Make this Python repository pass the dependency audit (no banned dependencies) and write the findings report. Use when asked to fix, audit, or report on the repository's dependencies.
---

# Dependency audit and repair

Run every command with Bash from the repository root, one `py` command per
call (the host permits only commands that start with `py`). `S` is
`.claude/skills/dep-audit`.

1. Run the check: `py -3 S/check_deps.py . --out .dep-audit/findings.json`.
2. If the verdict is `blocked`, repair: change each banned pin in
   `requirements.txt` to a non-banned version of the same package. Never
   delete the dependency and never edit the findings file. Then run the
   check again (step 1). Repeat until the verdict is `clean`.
3. Only when the latest check is clean, write `REPORT.md` in the
   repository root containing exactly the contents of
   `.dep-audit/findings.json`.
4. Report the final verdict.
