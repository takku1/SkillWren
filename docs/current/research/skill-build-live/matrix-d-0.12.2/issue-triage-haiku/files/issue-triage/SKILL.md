---
name: issue-triage
description: Label an issue as bug, feature or question, asking the user when the label is unclear, and write the label and a one-line reason to triage.md. Use when asked to triage, label or classify an issue. Never closes or edits the issue.
---

# Issue triage

This skill only reads the issue text and writes `triage.md`. It never closes
the issue and never edits it.

```contract
inputs:
  issue
```

```logic
issue-triage:
  require issue exists
    otherwise:
      abort with "Paste the issue text to triage."

  generate label from issue as label
  if the label is unclear from the issue:
    ask user to choose the label as bug, feature or question
    require user chooses the label
      otherwise:
        abort with "No label chosen; triage.md was not written."

  verify the label is exactly bug, feature or question from label
    otherwise:
      abort with "The label must be bug, feature or question."

  generate triage with a one-line reason from issue and label as triage
  write triage with triage_file
  return triage as triage
```

## Step meanings

- **triage_file**: `triage.md` in the working directory. Each run replaces
  its contents with the new line.
