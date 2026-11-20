---
name: issue-triage
description: Label an issue's text as bug, feature or question, asking the user when the label is unclear, and append the label and a one-line reason to triage.md. Use when asked to triage, label or classify an issue. Never closes or edits the issue.
---

# Issue triage

```contract
inputs:
  issue
```

```logic
issue-triage:
  require issue text exists
    otherwise:
      abort with "Paste the issue text to triage."

  generate triage from issue as triage
  if the label in triage is unclear:
    ask user for the label as chosen
    require chosen is bug, feature or question
      otherwise:
        abort with "No valid label chosen; triage.md was not written."
    apply label choice with chosen as triage

  generate entry from triage as entry
  write entry with triage_file
  return entry as entry
```

## Step meanings

- **triage**: the label, exactly one of bug, feature or question, and a one-line reason: a single sentence naming what in the issue text decided the label.
- **label**: the label in triage is unclear when the issue text supports two or more of bug, feature or question equally.
- **label choice**: the user's answer, accepted as the label only when it is exactly bug, feature or question. The reason in triage is kept.
- **entry**: one markdown line in the form `- <label>: <reason>`.
- **triage_file**: `triage.md` in the working directory, appended with one line per issue. This skill writes only this file; it never closes or edits the issue.
