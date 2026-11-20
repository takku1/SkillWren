---
skill: changelog-entry
name: changelog-entry
description: Add one entry to CHANGELOG.md under Unreleased for a change the user describes, in the Added, Fixed or Changed section, ending with its pull request number. Use when asked to add, record or write a changelog entry.
purpose: Add exactly one approved changelog entry, ending with its pull request number, to CHANGELOG.md and nothing else.
version: 0.1
accepts:
  request: { type: Text, required: true }
produces:
  entry: { type: Text }
owns-when:
  - user wants to add, record or write a changelog entry
  - user describes a change that belongs in CHANGELOG.md
requires:
  changelog-entry: [request exists]
flows: [changelog-entry]
authority:
  user-decides: [the pull request number, approve the entry]
  system-decides: [whether the request names a section and a pull request number]
  system-may: [read CHANGELOG.md]
  system-must-not: [write any file other than CHANGELOG.md, infer user approval, write before approval]
effects:
  reads: [changelog_file]
  creates: []
  mutates: [changelog_file]
risk: low
cost: cheap
budget: { header: 400, body: 1500 }
---

# Changelog entry

Adds one entry to `CHANGELOG.md`. The procedure below is the whole skill.

```contract
resources:
  changelog_file:
    path: CHANGELOG.md
    access: read+write
always:
  read CHANGELOG.md before any change to it
  end the entry with the pull request number in parentheses, such as (#123)
never:
  edit any file other than CHANGELOG.md
  write the entry before the user approves it
order:
  ask user to approve the entry before write entry
```

```logic
changelog-entry:
  require request exists
    otherwise:
      abort with "Describe the change, and give its pull request number if you have it."

  read changelog from changelog_file as current
    otherwise:
      abort with "CHANGELOG.md was not found in the working directory; nothing was changed."

  verify current has an Unreleased section from current
    otherwise:
      abort with "CHANGELOG.md has no Unreleased section; nothing was changed."

  label section_check:
  verify the request names one section: Added, Fixed or Changed from request
    otherwise:
      ask user for the section as section
      apply name section with section as request
      return to section_check

  label pr_check:
  verify the request names a pull request number from request
    otherwise:
      ask user for the pull request number as pr_number
      apply attach pull request number with pr_number as request
      return to pr_check

  generate entry from request as entry
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; CHANGELOG.md was not changed."

  write entry with changelog_file
  return entry as entry
```

## Step meanings

- **name section**: put the user's answer (Added, Fixed or Changed) into the request, so the entry lands in that subsection.
- **attach pull request number**: put the user's pull request number into the request, so the entry ends with it in the form (#N).
- **changelog_file insertion**: writing the approved entry means inserting it, as one bullet ending in (#N), at the end of the section the request names (Added, Fixed or Changed) under `## Unreleased`. Create the subsection under `## Unreleased` if it is missing, and change nothing else in the file.

## Appendix

The entry is one line in the style of the existing entries in CHANGELOG.md: past tense, starting with a capital letter, describing what changed for the user rather than how it was coded. It ends with the pull request number in the form (#N), with no trailing period after the parenthesis.
