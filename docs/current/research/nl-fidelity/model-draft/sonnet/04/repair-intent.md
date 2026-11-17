# Intent 04: evidence-backed publish

Run the test suite, verify the report from the check output shows no
failures, then publish the release notes. Do not publish if the report
is missing or failing.


Your previous draft was:

# Evidence-backed publish

```contract
inputs:
  release_notes
order:
  exec#tests before verify#report_present
  verify#report_present before verify#no_failures
  verify#no_failures before write#publish
```

```logic
publish-release-notes:
  require release_notes exists
    otherwise:
      abort with "Release notes are required."

  exec #tests test suite from checks as report

  verify #report_present report exists from report
    otherwise:
      abort with "Test report is missing; release notes not published."

  verify #no_failures report shows no failures from report
    otherwise:
      abort with "Test report shows failures; release notes not published."

  write #publish release_notes with publication

  return release_notes as published
```


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\04\draft.md:28: error P1: 'write #publish release_notes with publication' can run before 'verify#no_failures' (order rule, line 9) -- Make `verify#no_failures` (or a run that always performs it) complete on every path to this statement.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\04\draft.md:7: warning W13: order rule never applies: no statement starts with 'verify#report_present' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\04\draft.md:8: warning W13: order rule never applies: no statement starts with 'verify#no_failures' -- Fix the pattern so it matches the later statement, or drop the rule.

Return a corrected full fragment that fixes these errors without changing what the intent requires.
