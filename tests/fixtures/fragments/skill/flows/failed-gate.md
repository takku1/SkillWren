# A failed gate establishes nothing

```contract
order:
  verify checks passed before write report
```

```logic
close:
  verify checks passed
    otherwise:
      show checks
  write report with run_log
  return report as report
```
