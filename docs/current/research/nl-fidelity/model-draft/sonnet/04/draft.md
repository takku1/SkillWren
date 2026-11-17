# Evidence-backed publish

```contract
inputs:
  release_notes
order:
  exec#tests before verify report exists
  verify report exists before verify report shows no failures
  verify report shows no failures before write#publish
```

```logic
publish-release-notes:
  require release_notes exists
    otherwise:
      abort with "Release notes are required."

  exec #tests test suite from checks as report

  verify report exists from report
    otherwise:
      abort with "Test report is missing; release notes not published."

  verify report shows no failures from report
    otherwise:
      abort with "Test report shows failures; release notes not published."

  write #publish release_notes with publication

  return release_notes as published
```
