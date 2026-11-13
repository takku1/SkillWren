# Proposed workflow (STUB - placeholders must be replaced)

```contract
order:
  verify#result before write#note
```

```logic
draft:
  exec run the check from checks as result
  verify #result result meets the criterion from result
    otherwise:
      abort with "Criterion not met."
  write #note findings note with target
  return note as note
```
