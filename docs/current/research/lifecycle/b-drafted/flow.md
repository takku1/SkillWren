# README command coverage (revised from stub proposal)

Answers to the stub's questions: the check is `check_readme.py <subject>`
emitting `{"undocumented": [...], "verdict": ...}` and exiting nonzero on
gaps; passing means verdict `clean`; the note goes to the guarded
`COVERAGE.md` target; a check that cannot run aborts before verification.

```contract
order:
  verify#coverage before write#note
```

```logic
audit:
  exec readme coverage check from checks as findings
  verify #coverage findings show no undocumented commands from findings
    otherwise:
      abort with "Undocumented commands found."
  write #note coverage note with target
  return note as note
```
