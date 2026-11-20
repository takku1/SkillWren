---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added, Changed or Fixed, ending with the pull request number like (#123). Use when asked to add, write or record a changelog entry.
---

# Changelog entry

```contract
inputs:
  request, pr_number
order:
  exec readonly changelog read before ask user to choose the section
  exec readonly changelog read before generate entry
  show entry before write entry
  ask user to approve the entry before write entry
```

```logic
changelog-entry:
  require request exists
    otherwise:
      ask user for the change description as request
      retry

  exec readonly changelog read from tools as changelog
  verify #changelog the changelog was read and its headings are known from changelog
    otherwise:
      abort with "Could not read CHANGELOG.md; nothing was written."

  if the description does not make clear whether the entry is Added, Changed or Fixed:
    ask user to choose the section: Added, Changed or Fixed
    require user chooses the section
      otherwise:
        abort with "No section chosen; nothing was written."

  require pr_number exists
    otherwise:
      ask user for the pull request number as pr_number
      retry

  generate entry from request as entry
  apply entry format with changelog as entry
  apply pull request suffix with pr_number as entry

  label approving:
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      ask user for the changes to the entry as corrections
      apply entry revision with corrections as entry
      return to approving

  write entry with changelog_file
  return entry as entry
```

| Step | Command |
|---|---|
| `exec readonly changelog read` | `cat CHANGELOG.md` |

## Step meanings

- **tools**: the shell.
- **changelog_file**: `CHANGELOG.md` in the working directory. It is the only
  file this skill may write. Never edit, create or delete any other file.
- **entry format**: one line, matching the style of the entries already in the
  changelog, placed under the Added, Changed or Fixed heading (add the heading
  if it is missing). Do not rewrite other entries.
- **pull request suffix**: end the entry with the pull request number in
  parentheses, like `(#123)`.
- **entry revision**: apply the user's corrections to the entry, keep the
  trailing `(#123)` pull request number, and show it again.
