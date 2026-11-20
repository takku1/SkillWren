---
name: issue-triage
description: Label an issue as bug, feature or question from its text, ask the user when the label is unclear, and write the label and a one-line reason to triage.md. Never closes or edits the issue. Use when asked to triage an issue.
---

# Issue triage

```contract
inputs:
  issue_text
order:
  generate verdict before write verdict
  never write * with triage_file before generate verdict
```

```logic
issue-triage:
  require issue_text exists
    otherwise:
      abort with "Give the issue's text to triage."

  generate verdict from issue_text as verdict

  if the verdict is unclear, or the text plausibly fits more than one label:
    show verdict
    ask user to choose the label: bug, feature or question
    require user chooses one of bug, feature or question
      otherwise:
        abort with "No label chosen; nothing was written."
    apply user label with verdict as verdict

  write verdict with triage_file
  return verdict as verdict
```

## Step meanings

- **verdict**: exactly one label, `bug`, `feature` or `question`, plus a reason of one line with no line breaks, based only on the issue text.
- **user label**: replace the label with the user's choice and rewrite the reason in one line to match it.
- **triage_file**: `triage.md` in the current working directory, overwritten, containing `label: <label>` then `reason: <one line>`.

## Limits

This skill only reads the issue text and writes `triage.md`. It never closes, edits, comments on or relabels the issue, and never calls an issue tracker.
