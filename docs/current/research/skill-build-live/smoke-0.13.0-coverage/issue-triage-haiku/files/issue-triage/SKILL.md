---
name: issue-triage
description: Label an issue as bug, feature or question from its text, asking the user when the label is unclear, and record the label with a one-line reason in triage.md. Use when asked to triage, label or classify an issue. Never closes or edits the issue.
---

# Issue triage

This skill only reads the issue text it is given and writes `triage.md`.
It never closes, edits, comments on or otherwise changes the issue.

```contract
inputs:
  issue_text
order:
  require label before write entry
```

```logic
issue-triage:
  require issue_text exists
    otherwise:
      abort with "Paste the issue text to triage."

  generate label from issue_text as proposal
  apply label clarity with proposal as clarity

  if the label is unclear:
    ask user for the label as label
  else:
    apply proposed label with proposal as label

  require label is bug, feature or question
    otherwise:
      abort with "The label must be bug, feature or question; triage.md was not written."

  generate reason from issue_text and label as reason
  generate entry from label and reason as entry
  write entry with triage_file
  return entry as entry
```

## Step meanings

- **label clarity**: answer `clear` when the issue text supports exactly one
  of bug, feature or question; answer `unclear` when it fits more than one
  or none of them.
- **proposed label**: keep the proposal unchanged; it is one of bug,
  feature or question.
- **triage_file**: `triage.md` in the current working directory. Append
  one line per issue: `<label>: <reason>`.
