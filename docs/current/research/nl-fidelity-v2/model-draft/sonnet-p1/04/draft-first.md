```contract
resources:
  checks:
    path: the project test suite command
    access: execute
  release_notes:
    path: the release notes
    access: write
inputs:
  release_notes_text
order:
  verify #report_clean before write #publish
```

```logic
publish-release-notes:
  require release_notes_text exists
    otherwise:
      abort with "Release notes are required."

  exec checks from checks as results

  verify #report_clean the report shows no failures from results
    otherwise:
      abort with "Report is missing or failing; not publishing."

  write #publish release_notes_text with release_notes

  return release_notes_text as published
```