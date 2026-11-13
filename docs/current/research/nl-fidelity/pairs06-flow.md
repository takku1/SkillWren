# Batch 2: approvals, chains, branches, repair, multi-write

```contract
order:
  ask#first before ask#second
  ask#second before write#final
  verify#a before write#b
  write#b before write#c
  verify#suite before write#log
  write#log before write#notes
```

Two sequential human approvals before any write.

```logic
f06:
  ask #first user to approve the plan
  require confirmation
    otherwise:
      abort with "Plan rejected."
  ask #second user to approve the budget
  require confirmation
    otherwise:
      abort with "Budget rejected."
  write #final approved plan with target
  return plan as plan
```

A three-step chain with two order rules.

```logic
f07:
  exec first check from checks as first
  verify #a first check passed from first
    otherwise:
      abort with "First check failed."
  write #b first result with logfile
  write #c summary with target
  return summary as summary
```

Branch on a warm cache with a cold-cache abort.

```logic
f08:
  require request exists
    otherwise:
      abort with "No request."
  unless cache is warm:
    exec cache warm from checks as cache
    verify #cache cache is warm from cache
      otherwise:
        abort with "Cache cold."
  return request as request
```

Repair loop in the backup domain.

```logic
f09:
  exec backup check from checks as state
  verify #backup backup is complete from state
    otherwise:
      apply backup repair with state as state
      exec backup check from checks as state
      verify #recheck backup is complete from state
      retry
  return state as state
```

## Step meanings

- **backup repair**: rerun the backup and refresh its state.

Two writes after one evidence-anchored verification.

```logic
f10:
  exec suite check from checks as report
  verify #suite suite is green from report
    otherwise:
      abort with "Red suite."
  write #log test log with logfile
  write #notes release notes with target
  return notes as notes
```
