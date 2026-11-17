# Batch 2 intents

f06: Approving a plan takes two humans: one approves the plan, another
approves the budget. Either rejection stops everything; only a
twice-approved plan is written.

f07: A three-step chain: run the first check, verify it passed, write the
first result, then write the summary. Each step depends on the previous
one completing.

f08: When the cache is not warm, run the warm-up check and verify it.
A cold cache aborts. A warm cache skips all of that and returns
the request unchanged.

f09: Backups must be complete. Check, and on failure repair, recheck,
and retry until complete. Only then return the state.

f10: The suite must be green before anything is published: run it,
verify the report, write the test log, then write the release notes.
