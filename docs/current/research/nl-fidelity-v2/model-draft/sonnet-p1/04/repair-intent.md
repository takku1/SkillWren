# Intent 04: evidence-backed publish

Run the test suite, verify the report from the check output shows no
failures, then publish the release notes. Do not publish if the report
is missing or failing.


Your previous draft was:

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

`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:2: error F2: unexpected 'resources:' in contract block -- Only always:/never:/inputs:/order: live here.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:3: error F2: contract line outside any section -- Place it under resources:/always:/never:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:4: error F2: contract line outside any section -- Place it under resources:/always:/never:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:5: error F2: contract line outside any section -- Place it under resources:/always:/never:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:6: error F2: contract line outside any section -- Place it under resources:/always:/never:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:7: error F2: contract line outside any section -- Place it under resources:/always:/never:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\04\draft.md:8: error F2: contract line outside any section -- Place it under resources:/always:/never:.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
