---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added or Fixed, after showing the entry and getting approval. Use when asked to add, write or log a changelog entry.
---

# Changelog entry

```contract
inputs:
  request
order:
  verify #changelog before generate entry
  verify #changelog before ask user to choose
  ask user to approve the entry before write entry
```

```logic
changelog-entry:
  require request exists
    otherwise:
      abort with "Describe the change to add to the changelog."

  read changelog from changelog_file as changelog
    otherwise:
      abort with "CHANGELOG.md was not found; nothing was written."
  verify #changelog the current CHANGELOG.md content was loaded from changelog
    otherwise:
      abort with "CHANGELOG.md could not be read; nothing was written."

  if the description does not make clear whether the entry belongs under Added or Fixed:
    ask user to choose whether the entry belongs under Added or Fixed
    require user chooses Added or Fixed
      otherwise:
        abort with "No section chosen; nothing was written."

  generate entry from changelog as entry
  apply section placement with request as entry
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; nothing was written."

  write entry with changelog_file
  return entry as entry
```

## Step meanings

- **changelog_file**: `CHANGELOG.md` in the working directory. It is the only file this skill may write; never edit any other file.
- **section placement**: put the entry under the Added or Fixed heading (the user's choice, or the one the description makes clear), at the top of that section's list of the newest release, matching the existing entries' wording, tense and bullet style. Add exactly one entry; leave all other lines unchanged.
