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


Your previous draft was:

# Batch 2 flows

```contract
inputs:
  plan, summary, request, state, release_notes
order:
  ask#plan_approval before write#plan_write
  ask#budget_approval before write#plan_write
  verify#first_passed before write#first_result
  write#first_result before write#summary_write
  verify#cache_warm before return#cache_ok
  verify#backups_complete before return#backup_state
  verify#suite_green before write#test_log
  write#test_log before write#release_notes_write
```

```logic
f06:
  ask #plan_approval plan approver to approve plan
  require confirmation
    otherwise:
      abort with "Plan rejected."
  ask #budget_approval budget approver to approve budget
  require confirmation
    otherwise:
      abort with "Budget rejected."
  write #plan_write plan with plan_store
  return plan as plan

f07:
  exec first check from checks as first
  verify #first_passed first check passed from first
    otherwise:
      abort with "First check failed."
  write #first_result first with first_result_file
  write #summary_write summary with summary_file
  return summary as summary

f08:
  if cache is not warm:
    exec warm-up check from checks as warmup
    verify #cache_warm cache is warm from warmup
      otherwise:
        abort with "Cache is cold."
  return #cache_ok request as request

f09:
  exec backup completeness check from checks as backups
  verify #backups_complete backups are complete from backups
    otherwise:
      apply backup repair with state as state
      exec backup completeness check from checks as backups
      retry
  return #backup_state state as state

f10:
  exec test suite from checks as report
  verify #suite_green suite is green from report
    otherwise:
      abort with "Suite is not green."
  write #test_log report with test_log
  write #release_notes_write release_notes with release_notes_file
  return release_notes as release_notes
```

## Step meanings

- **backup repair**: repair the backups the check reported as incomplete, applying the repair to the state before rechecking.


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:30: error V1: unknown statement 'f07:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:31: error O1: 'exec first check from checks as first' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:32: error O1: 'verify #first_passed first check passed from first' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:35: error O1: 'write #first_result first with first_result_file' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:36: error O1: 'write #summary_write summary with summary_file' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:37: error O1: 'return summary as summary' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:39: error V1: unknown statement 'f08:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:40: error O1: 'if cache is not warm:' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:45: error O1: 'return #cache_ok request as request' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:45: error V1: malformed return 'return #cache_ok request as request' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:47: error V1: unknown statement 'f09:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:48: error O1: 'exec backup completeness check from checks as backups' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:49: error O1: 'verify #backups_complete backups are complete from backups' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:54: error O1: 'return #backup_state state as state' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:54: error V1: malformed return 'return #backup_state state as state' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:56: error V1: unknown statement 'f10:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:57: error O1: 'exec test suite from checks as report' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:58: error O1: 'verify #suite_green suite is green from report' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:61: error O1: 'write #test_log report with test_log' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:62: error O1: 'write #release_notes_write release_notes with release_notes_file' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:63: error O1: 'return release_notes as release_notes' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:7: warning W13: order rule never applies: no statement starts with 'write#plan_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:8: warning W13: order rule never applies: no statement starts with 'write#plan_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:9: warning W13: order rule never applies: no statement starts with 'write#first_result' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:10: warning W13: order rule never applies: no statement starts with 'write#summary_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:11: warning W13: order rule never applies: no statement starts with 'return#cache_ok' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:12: warning W13: order rule never applies: no statement starts with 'return#backup_state' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:13: warning W13: order rule never applies: no statement starts with 'write#test_log' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:14: warning W13: order rule never applies: no statement starts with 'write#release_notes_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:30: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:31: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:31: warning W5: binding 'first' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:32: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:33: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:34: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:35: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:36: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:37: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:39: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:40: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:41: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:41: warning W5: binding 'warmup' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:42: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:43: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:44: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:45: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:47: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:48: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:48: warning W5: binding 'backups' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:49: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:50: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:51: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:51: warning W5: binding 'state' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:52: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:53: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:54: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:56: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:57: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:57: warning W5: binding 'report' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:58: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:59: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:60: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:61: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:62: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs06\draft.md:63: warning W10: unreachable statement -- Remove it or fix the control flow.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
