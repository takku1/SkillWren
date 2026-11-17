---
name: dep-audit
description: Audit this Python repository for banned dependencies and unallowlisted licenses, then write the findings report only through the guard after verification passes. Use when asked to audit, check, or report on the repository's dependencies.
---

# Dependency audit

Run the dependency check, verify that its findings show no banned
dependencies, and write the findings report only after verification
passes. You never write the report file yourself: the host guard writes
it, and only after its verifier accepts the exact candidate bytes. Never
submit a write when verification fails.

Run every command with Bash from the repository root. `S` is this
skill's directory, `.claude/skills/dep-audit`. `SW` is the SkillWren CLI,
`py -3 Z:/SkillWren/scripts/skillwren.py`. Use forward slashes. The host permits only commands
that start with `py`: issue each command below as its own Bash call,
spelled out in full, with no shell variables, `&&`, `;`, or pipes.
Ledger step names must be exactly as written.

1. Confirm approval: `SW approve --check S/flow.md --dir S/approvals`.
   If it does not print `"approved": true`, stop and report that the
   procedure is not approved.
2. Open a run: `SW ledger start S/flow.md --label dep-audit --require "dependency check ran" --require "verify#deps" --require "write#report"`.
   Note the run id it prints.
3. Run the check as recorded evidence:
   `SW ledger exec <run> --step "dependency check ran" -- py -3 S/check_deps.py . --out .dep-audit/candidate.json`
4. Verify as recorded evidence:
   `SW ledger exec <run> --step "verify#deps" -- py -3 S/verify_findings.py .dep-audit/candidate.json`
   If it exits non-zero, abort: report "Blocked findings." with the
   banned items from the candidate, run `SW ledger check <run>`, and stop.
   Do not build or submit guard requests.
5. Write through the guard:
   `py -3 S/make_requests.py .dep-audit/candidate.json .dep-audit/requests.jsonl`
   then `py -3 S/guard_submit.py .dep-audit/requests.jsonl`.
   Both responses must be `"ok": true`; the last line names the target.
6. Record the effect: `SW ledger note <run> --step "write#report" --artifact <target>`.
7. Check the run: `SW ledger check <run> --require-evidence --require-completeness`
   and report its verdict with the findings.
