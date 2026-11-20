---
name: issue-triage
description: Label one issue as bug, feature or question and append the label with a one-line reason to triage.md. Asks the user when the label is unclear. Never closes or edits the issue. Use when asked to triage, label or classify an issue.
---

# Issue triage

Labels a single issue and records the result. The issue itself is read-only.

```contract
inputs:
  issue
```

```logic
issue-triage:
  require issue exists
    otherwise:
      abort with "Paste the text of the issue to triage."

  generate label from issue as classification
  if classification is unclear:
    ask user for the label as clarification
    require clarification is bug, feature or question
      otherwise:
        abort with "No valid label chosen; triage.md was not written."
    apply label choice with clarification as classification


  generate triage line from classification and issue as line
  write line with triage_file

  return #triaged:
    label = classification
    reason = line
```

## Step meanings

- **issue**: the text of one issue, supplied by the user. Read-only: this
  skill never closes, edits, comments on, or labels the issue on the host.
- **label**: exactly one of `bug`, `feature`, `question`. A bug reports
  behaviour that is wrong against what was expected; a feature asks for
  new behaviour; a question asks how something works or for information.
- **label choice**: the user's answer to the clarification question, taken
  as the label. It must be `bug`, `feature` or `question`; any other answer
  stops the run without writing.
- **triage line**: `<label>: <reason>`, where the reason is one sentence
  that states why the label fits the issue.
- **triage_file**: `triage.md` in the working directory. Each run appends
  one line; existing lines are kept.
