# Intent 04: evidence-backed publish

Run the test suite, verify the report from the check output shows no
failures, then publish the release notes. Do not publish if the report
is missing or failing.


Your previous draft was:

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


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\04\draft.md:17: error P1: 'write #publish release_notes with release_notes_destination' can run before 'verify#report_clean' (order rule, line 6) -- Make `verify#report_clean` (or a run that always performs it) complete on every path to this statement.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\04\draft.md:5: warning W13: order rule never applies: no statement starts with 'verify#report_clean' -- Fix the pattern so it matches the later statement, or drop the rule.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
