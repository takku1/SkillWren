---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added, Changed or Fixed, ending with the pull request number. Use when asked to add, write or log a changelog entry.
---

# Changelog entry

```contract
inputs:
  request
order:
  verify #section before generate entry
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

  if request does not make clear whether the entry belongs under Added, Changed or Fixed:
    ask user to choose the category Added, Changed or Fixed for the entry
    require user chooses a category
      otherwise:
        abort with "No category chosen; nothing was written."
    apply category choice with request as category
  else:
    generate category from request as category

  verify #section the changelog has a section for the category from changelog
    otherwise:
      abort with "CHANGELOG.md has no section for that category; nothing was written."

  if request gives no pull request number:
    ask user for the pull request number as pr_number
  else:
    generate pr_number from request as pr_number

  generate entry from request as entry
  apply category wording with category as entry
  apply entry format with changelog as entry
  verify #format the entry is one line in the style of the existing entries and ends with the pull request number in parentheses, like (#123) from entry
    otherwise:
      apply entry format with pr_number as entry
      retry

  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; nothing was written."

  write entry with changelog_file
  return entry as entry
```

## Step meanings

- **changelog_file**: `CHANGELOG.md`. It is the only file this skill may change; never edit or create any other file.
- **category choice**: set the category to the one the user chose.
- **category wording**: make the entry read naturally for its category (Added: a new capability; Changed: a modified behaviour; Fixed: a corrected defect).
- **entry format**: one line, written like the existing entries in the changelog, ending with the pull request number in parentheses, like `(#123)`.
- **write entry**: insert exactly the approved entry, once, at the end of the chosen category's section; change nothing else in the file.
