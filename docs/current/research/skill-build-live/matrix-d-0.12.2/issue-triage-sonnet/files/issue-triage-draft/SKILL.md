---
name: issue-triage
description: Label an issue as bug, feature or question from its text, ask the user when the label is unclear, and record the label with a one-line reason in triage.md. Never closes or edits the issue. Use when asked to triage, label or classify an issue.
---

# Issue triage

```contract
inputs:
  issue_text
```

```logic
issue-triage:
  label intake:
  require issue_text exists
    otherwise:
      ask user for the issue text as issue_text
      return to intake

  generate triage from issue_text as triage
  apply triage format with triage as triage

  if the label in triage is unclear:
    show triage
    ask user to decide the label as bug, feature or question
    require user decides the label
      otherwise:
        abort with "No label chosen; triage.md was not changed."
    apply user label with triage as triage

  verify the label is exactly one of bug, feature or question and the reason is one line from triage
    otherwise:
      apply triage format with triage as triage
      retry

  write triage with triage_file
  return triage as triage
```

## Step meanings

- **triage**: choose exactly one label (`bug`: something that should work is broken; `feature`: a request for new or changed behaviour; `question`: a request for information or help) and a one-line reason. Mark the label unclear when the text fits more than one label or none.
- **triage format**: one label from `bug`, `feature`, `question` (or `unclear`) and a reason on a single line.
- **user label**: replace the label with the user's choice and rewrite the reason in one line to match it.
- **triage_file**: `triage.md` in the working directory. Append the entry as `- <label>: <reason>`; never overwrite earlier entries. This is the only thing the skill writes. It never closes, comments on, labels or edits the issue or its tracker.
