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
  plan, summary, request, state
order:
  ask#plan_approval before write#plan_write
  ask#budget_approval before write#plan_write
  exec first check before verify#first_passed
  verify#first_passed before write#first_write
  write#first_write before write#summary_write
  exec suite before verify#suite_green
  verify#suite_green before write#test_log
  write#test_log before write#release_notes
```

```logic
f06:
  ask #plan_approval reviewer to approve plan
  require confirmation
    otherwise:
      abort with "Plan rejected."

  ask #budget_approval budget approver to approve budget
  require confirmation
    otherwise:
      abort with "Budget rejected."

  write #plan_write plan with plan_store
  return plan as plan
```

```logic
f07:
  exec first check from checks as first_result
  verify #first_passed first check passed from first_result
    otherwise:
      abort with "First check failed."

  write #first_write first_result with results
  write #summary_write summary with summaries
  return summary as summary
```

```logic
f08:
  unless cache is warm:
    exec warm-up check from checks as warmup
    verify cache is warm from warmup
      otherwise:
        abort with "Cache is cold."

  return request as request
```

```logic
f09:
  exec backup check from checks as backup_status
  verify backups are complete from backup_status
    otherwise:
      exec backup repair from checks as repair_result
      exec backup check from checks as backup_status
      retry

  return state as state
```

```logic
f10:
  exec suite from checks as report
  verify #suite_green suite is green from report
    otherwise:
      abort with "Suite is not green."

  write #test_log report with test_logs
  write #release_notes release_notes with publication
  return release_notes as release_notes
```


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:77: error U1: return value 'release_notes' is not bound -- Bind it with `as` or list it under the contract's inputs:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:7: warning W13: order rule never applies: no statement starts with 'write#plan_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:8: warning W13: order rule never applies: no statement starts with 'write#plan_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:9: warning W13: order rule never applies: no statement starts with 'verify#first_passed' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:10: warning W13: order rule never applies: no statement starts with 'write#first_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:11: warning W13: order rule never applies: no statement starts with 'write#summary_write' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:12: warning W13: order rule never applies: no statement starts with 'verify#suite_green' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:13: warning W13: order rule never applies: no statement starts with 'write#test_log' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:14: warning W13: order rule never applies: no statement starts with 'write#release_notes' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs06\draft.md:61: warning W5: binding 'repair_result' never referenced -- Use it or drop the `as`.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
