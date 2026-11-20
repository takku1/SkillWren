---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added, Fixed or Changed, ending with the PR number like (#123). Use when asked to add, write or log a changelog entry.
---

# Changelog entry

```contract
inputs:
  request
order:
  verify #loaded before generate entry
  ask user to approve the entry before write entry
```

```logic
changelog-entry:
  require request exists
    otherwise:
      abort with "Describe the change to add to the changelog."

  read current changelog from changelog_file as changelog
    otherwise:
      abort with "CHANGELOG.md was not found, so nothing was changed."

  if the description does not make clear whether the entry is Added, Fixed or Changed:
    ask user for the section, one of Added, Fixed or Changed as section
  else:
    generate section from request as section

  verify #loaded the changelog was read and has a heading for the chosen section from changelog
    otherwise:
      abort with "CHANGELOG.md has no heading for that section, so nothing was changed."

  if the request has no pull request number:
    ask user for the pull request number as pr_number
  else:
    generate pr_number from request as pr_number

  generate entry from request as entry
  apply existing style with changelog as entry
  apply section placement with section as entry
  apply entry format with pr_number as entry
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; nothing was written."

  write entry with changelog_file
  return entry as entry
```

## Step meanings

- **changelog_file**: `CHANGELOG.md` in the working directory. It is the only file this skill may write or edit; never touch any other file.
- **existing style**: rewrite the entry as one line in the style of the existing entries in the changelog (tense, punctuation, bullet marker).
- **section placement**: mark the entry as belonging under the chosen section's heading in the existing file.
- **entry format**: end the entry with the PR number in parentheses, like `(#123)`. The shown entry is the exact text written.
