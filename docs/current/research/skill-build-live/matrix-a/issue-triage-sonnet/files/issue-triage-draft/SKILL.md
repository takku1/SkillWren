---
name: issue-triage
description: Label an issue as bug, feature or question from its text, ask the user when the label is unclear, and append the label with a one-line reason to triage.md. Never closes or edits the issue. Use when asked to triage, label or classify an issue.
---

# Issue triage

This skill only reads the issue text it is given and writes to `triage.md`. It never closes, edits, comments on or relabels the issue, and runs no issue-tracker command.

```contract
inputs:
  issue_text
```

```logic
issue-triage:
  require issue_text exists
    otherwise:
      abort with "Paste the issue's text to triage."

  generate label and reason from issue_text as verdict
  if the label is unclear, because the text fits more than one of bug, feature and question or none of them:
    show verdict
    ask user to choose the label: bug, feature or question
    require user chooses the label
      otherwise:
        abort with "No label chosen; triage.md was not changed."
    apply user label with verdict as verdict

  apply one-line reason with verdict as entry
  write entry with triage_file
  return entry as entry
```

## Step meanings

- **label and reason** (generate): pick exactly one of `bug` (something that should work but does not), `feature` (a request for new or changed behavior) or `question` (asking how something works or what to do). Give the reason in the issue's own terms.
- **user label**: replace the label with the user's choice and rewrite the reason to fit it.
- **one-line reason**: format the entry as `<label>: <reason>`, with the reason on a single line and no line breaks.
- **ordering**: when the label is unclear the question comes first, and a dismissed or unanswered question aborts with nothing written. The write to `triage.md` is the last step and the only mutation.
- **triage_file**: `triage.md` in the working directory. Append the entry as a new line and keep earlier entries. This is the only file the skill may write.
