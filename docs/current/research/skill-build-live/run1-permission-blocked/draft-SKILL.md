---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added or Fixed, after the user approves the wording. Use when asked to add, write or log a changelog entry.
---

# Changelog entry

```contract
inputs:
  request
order:
  read changelog before generate entry
  ask user to approve the entry before write entry
```

```logic
changelog-entry:
  require request exists
    otherwise:
      ask user for a description of the change as request

  read changelog from changelog_file as changelog
    otherwise:
      abort with "CHANGELOG.md was not found; nothing was changed. Ask the user how to proceed."

  unless request makes clear whether the change is Added or Fixed:
    ask user to decide whether the entry belongs under Added or Fixed
    require user decides Added or Fixed
      otherwise:
        abort with "No section chosen; nothing was written."

  generate entry from request and changelog as entry
  apply changelog style with changelog as entry

  label reviewing:
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      ask user for the changes to the entry as edits
      apply entry revision with edits as entry
      return to reviewing

  write entry with changelog_file
  return entry as entry
```

## Step meanings

- **changelog_file**: `CHANGELOG.md` in the working directory. It is the only file this skill may write. Never edit any other file.
- **changelog style**: match the existing file's heading, bullet and wording style. Offer only the Added and Fixed sections. Place the entry under the chosen section and create no other section.
- **entry revision**: change the entry as the user asked, then show it again.
