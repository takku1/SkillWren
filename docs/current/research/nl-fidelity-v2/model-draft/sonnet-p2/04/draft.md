```contract
inputs:
  release_notes, release_notes_destination
order:
  exec test suite before verify#reportclean
  verify#reportclean before write#publish
```

```logic
publish-release-notes:
  exec test suite from checks as report

  verify #reportclean the report exists and shows no failures from report
    otherwise:
      abort with "Report is missing or failing; release notes not published."

  write #publish release_notes with release_notes_destination

  return release_notes as published
```