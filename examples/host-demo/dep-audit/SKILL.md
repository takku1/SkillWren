---
name: dep-audit
description: Audit this Python repository for banned dependencies and unallowlisted licenses, then write the findings report only through the guard after verification passes. Use when asked to audit, check, or report on the repository's dependencies.
---

# Dependency audit (SkillWren logic)

The procedure is the `logic` block below, with its `contract` order rule
(a verbatim copy of the approved `flow.md`). Execute it exactly; it is the
only procedure.

All checks run before any write; the report is written only through
the guard after a clean verification.

```contract
order:
  verify#deps before write#report
```

```logic
audit:
  exec dependency check from checks as findings
  verify #deps findings show no banned dependencies from findings
    otherwise:
      abort with "Blocked findings."
  write #report audit findings with target
  return report as report
```

Run every command with Bash from the repository root, as its own call,
spelled out in full (the host permits only commands starting with `py`;
no shell variables, `&&`, `;`, or pipes). `S` = `.claude/skills/dep-audit`,
`SW` = `py -3 {SKILLWREN}`.

Before the flow: `SW approve --check S/flow.md --dir S/approvals` must print
`"approved": true`, then
`SW ledger start S/flow.md --label dep-audit --require "dependency check ran" --require "verify#deps" --require "write#report"`.

| Flow step | Command |
|---|---|
| `exec dependency check` | `SW ledger exec <run> --step "dependency check ran" -- py -3 S/check_deps.py . --out .dep-audit/candidate.json` |
| `verify #deps` (passes iff exit 0) | `SW ledger exec <run> --step "verify#deps" -- py -3 S/verify_findings.py .dep-audit/candidate.json` |
| `abort with` | report the message and the banned items, then `SW ledger check <run>` |
| `write #report` | `py -3 S/make_requests.py .dep-audit/candidate.json .dep-audit/requests.jsonl`, then `py -3 S/guard_submit.py .dep-audit/requests.jsonl` (all `"ok": true`; last line names the target), then `SW ledger note <run> --step "write#report" --artifact <target>` |
| `return` | `SW ledger check <run> --require-evidence --require-completeness`; report its verdict |
