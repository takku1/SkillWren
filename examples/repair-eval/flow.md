# Dependency audit with repair

Fix banned pins until the check is clean, then write the findings report
only after a clean verification of the current repository.

```contract
order:
  verify#deps before write#report
```

```logic
repair:
  exec dependency check from checks as findings
  verify #deps findings show no banned dependencies from findings
    otherwise:
      apply dependency repair with findings as findings
      exec dependency check from checks as findings
      retry
  write #report findings with target
  return findings as report
```

## Step meanings

- **dependency repair**: change each banned pin in `requirements.txt` to a
  non-banned version of the same package. Never delete the dependency and
  never edit the findings file.
