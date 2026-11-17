# Evidence-backed publish

The suite runs as evidence, the report is verified from that output,
and only a clean report is published.

```contract
order:
  verify#report before write#notes
```

```logic
publish:
  exec test suite from checks as report
  verify #report test report shows no failures
    otherwise:
      abort with "Failing tests."
  write #notes release notes with target
  return notes as notes
```
