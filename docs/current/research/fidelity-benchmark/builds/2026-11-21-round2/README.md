# Round 2, attempt 1: aborted by a usage limit

All five compiler builds (pinned at `f1a87b4`, SkillWren 0.13.3) failed in
the repair phase with `api_error_status: 429`, `usage_limit_reached`
(`compiler/<source>-stderr.txt`). That is an infrastructure failure, not a
compiler outcome, so this attempt measures nothing. It is kept as a record
and not scored. The whole round was rerun from scratch with the same commit
and configuration as `../2026-11-21-round2-attempt2/` (all five builds, not
a selective rerun).
