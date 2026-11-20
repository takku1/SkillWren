# Full-stack live use of SkillWren 0.10 to 0.11 (2026-11-20)

Third report from SkillWren's maintained consumer, after [2026-11-19](full-stack-live-use-2026-11-19.md). It is the owner's three-tier pipeline check for the 0.11 skill-load assurance change: rebuild full-stack on the new SkillWren, build in MochiOS with it, and feed findings back up. Sources in full-stack (branch `skillwren-0.11`, PR takku1/full-stack#2): `docs/design-decisions.md` D-025 and `docs/research/field-report-2026-11-20-mochios-5.md`. One session, Opus 5.5, author-scored.

## Results

| # | Tier | Finding | SkillWren action |
|---|---|---|---|
| 1 | full-stack | full-stack 0.8.3 passed unchanged on SkillWren 0.11 (98 tests, flows clean, `build` 0 warnings), so a plain rebuild exercised nothing new | None; adoption was needed to test anything |
| 2 | full-stack | Adding `never write * with design_docs before exec guard start` gave P3 twice on the 0.8.3 flows: the design note and assurance table were written before the guarded run started. That is field report 4's F-4 collision, which full-stack had fixed only in prose. The hint named both statements and the fix (do them after `start`). The restructure needed a new `deliver` flow, which the hint cannot propose | Evidence that P3 and its hint work on a real package; no change |
| 3 | full-stack | Pattern `*` mid-rule (`write * with design_docs`) let the rule name a target, not a verb, so the scratch-draft write in `assurance` stayed legal | None |
| 4 | full-stack | `ledger start --package` and a load record made `close` print "Package: the host loaded ... (same tree as this run's scripts)" in the live MochiOS run, and a test shows it refusing a stale cache (F-1) | Works as designed |
| 5 | SkillWren | full-stack's hook records the copy it runs from (`${CLAUDE_PLUGIN_ROOT}`), not a resolved guess, which removes the mirror SPEC 24 had to assume | **Adopted:** `ledger record-load --package DIR` |
| 6 | MochiOS | Build: reliable `WAIT_BLOCK` boot markers (flag claimed only after the write, bounded retries, printed outside the Gate lock). Two native boots, ledger `valid, complete` | Not SkillWren's |
| 7 | full-stack | Two guard defects from the build: no way to widen a write set (R-1), and assurance tables read file-wide (R-2) | Fixed in full-stack |

The guard's skill-load requirement (SPEC 24) was not exercised by full-stack, whose guard is advisory and runs as the agent. full-stack adopted the same idea as an opt-in hook rule (`git config fullstack.requireSkill true`). The host load in the MochiOS run was simulated (the installed plugin was 0.8.3), so the hook path is shown by full-stack's tests, not by the host.
