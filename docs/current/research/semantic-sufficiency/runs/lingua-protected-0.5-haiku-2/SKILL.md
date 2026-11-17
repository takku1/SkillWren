---
name: dep-audit
description: Audit this Python repository's dependencies against the banned list and write the findings report. Use when asked to audit, fix, or report on the repository's dependencies.
---


 
 audit 
 
 command Bash repository `py`command 
 call host permits start `py`. `S`
 `.claude/skills/dep-audit`. 
 
. `py -3 S/check_deps.py . --out .dep-audit/findings.json`. 
. audit read only `requirements.txt` `pyproject.toml`project file. Dependency changes need pull request not part task. 
. verdict `blocked`make pass report blocked findings banned items. 
. `REPORT.md`repository root containing contents `.dep-audit/findings.json`. 
. findings. 
. Report verdict. 
 
