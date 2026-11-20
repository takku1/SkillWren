---
name: issue-triage
description: Label an issue's text as bug, feature or question and write the label and a one-line reason to triage.md. Asks the user when the label is unclear. Use when asked to triage, label or classify an issue. Never closes or edits the issue.
---

# Issue triage

```contract
inputs:
  issue
```

```logic
issue-triage:
  require issue exists
    otherwise:
      abort with "Paste the issue text to triage."

  generate triage from issue as triage
  apply label rules with issue as triage

  if triage is unclear:
    ask user to choose the label for the issue
    require user chooses bug, feature or question
      otherwise:
        abort with "No label chosen; triage.md was not written."
    apply user label with triage as triage

  verify #label triage has one label from bug, feature or question and a one-line reason from triage
    otherwise:
      abort with "The triage could not be finished; triage.md was not written."

  write triage with triage_file
  return triage as triage
```

## Step meanings

- **label rules**: bug means the issue reports behaviour that is wrong or
  broken. feature means the issue asks for behaviour that does not exist
  yet. question means the issue asks how or why and requests no change.
  If the issue fits none of these, or more than one, set the label to
  unclear and say in the reason why. Reason is one line.
- **user label**: set the label to the one the user chose and set the
  reason to "Label chosen by user."
- **triage_file**: `triage.md` in the working directory. Each run appends
  one entry: the label, then the one-line reason. Nothing else is written.
