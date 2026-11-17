# Batch 2 flows

```contract
inputs:
  plan, summary, request, state, release_notes
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
      exec backup repair from checks
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
