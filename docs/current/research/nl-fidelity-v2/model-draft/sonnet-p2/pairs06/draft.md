# Batch 2 flows

```contract
inputs:
  plan, summary, request, state, release_notes
order:
  ask#plan_approval before write#plan_write
  ask#budget_approval before write#plan_write
  verify#first_passed before write#first_result
  write#first_result before write#summary_write
  verify#suite_green before write#test_log
  write#test_log before write#release_notes_write
```

f06: two human approvals, then write the plan.

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
```

f07: three-step chain.

```logic
f07:
  exec first check from checks as first
  verify #first_passed first check passed from first
    otherwise:
      abort with "First check failed."
  write #first_result first with first_result_file
  write #summary_write summary with summary_file
  return summary as summary
```

f08: warm-up only when the cache is cold.

```logic
f08:
  if cache is not warm:
    exec warm-up check from checks as warmup
    verify #cache_warm cache is warm from warmup
      otherwise:
        abort with "Cache is cold."
  return request as request
```

f09: backups must be complete.

```logic
f09:
  exec backup completeness check from checks as backups
  verify #backups_complete backups are complete from backups
    otherwise:
      apply backup repair with state as state
      exec backup completeness check from checks as backups
      verify backups are complete from backups
      retry
  return state as state
```

f10: green suite before publishing.

```logic
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
