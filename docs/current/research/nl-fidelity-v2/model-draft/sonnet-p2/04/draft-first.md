```contract
inputs:
  release_notes
order:
  exec test suite before verify#report_clean
  verify#report_clean before write#publish
```

```logic
publish-release-notes:
  exec test suite from checks as report

  verify #report_clean the report exists and shows no failures from report
    otherwise:
      abort with "Report is missing or failing; release notes not published."

  write #publish release_notes with release_notes_destination

  return release_notes as published
```
