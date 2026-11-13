---
name: dep-audit
description: Audit a Python repo for banned dependencies and unallowlisted licenses, then write the findings report only after verification passes.
---

# Dependency audit

Run the check, verify clean findings, and write the report through the
guard. The structured procedure is `flow.md` next to this file; its
meaning is `explanation.txt`, and its approval digest is in
`approvals/`. Never write the report when verification fails.
