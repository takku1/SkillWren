# Dependency audit with enforced reporting

All checks run before any write; the report is written only through
the guard after a clean verification.

```contract
order:
  verify#deps before write#report
```

```logic
audit:
  exec dependency check from checks as findings
  verify #deps findings show no banned dependencies from findings
    otherwise:
      abort with "Blocked findings."
  write #report audit findings with target
  return report as report
```
