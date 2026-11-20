---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added, Changed or Fixed in the Unreleased section, ending with its pull request number. Use when asked to add, record or write a changelog entry.
---

# Changelog entry

```contract
inputs:
  request
order:
  exec readonly changelog read before generate entry
  exec readonly changelog read before ask user
  ask user to approve the entry before write updated_changelog
```

```logic
changelog-entry:
  require request exists
    otherwise:
      abort with "Describe the change to record in the changelog."

  exec readonly changelog read from changelog_file as changelog
  verify #changelog the output contains a line starting with "## Unreleased" from changelog
    otherwise:
      abort with "CHANGELOG.md has no Unreleased section; nothing was written."

  if request names a pull request number:
    generate pr_number from request as pr_number
  else:
    ask user for the pull request number as pr_number
  require pr_number is a pull request number such as #123
    otherwise:
      abort with "A pull request number is required; nothing was written."

  if request makes the section clear as Added, Changed or Fixed:
    generate section from request as section
  else:
    ask user for the section as section
  require section is Added, Changed or Fixed
    otherwise:
      abort with "No section chosen; nothing was written."

  show pr_number
  show section
  generate entry from request and pr_number and section as entry
  apply place entry with changelog as updated_changelog
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; nothing was written."

  write updated_changelog with changelog_file
  return entry as entry
```

| Step | Command |
|---|---|
| `exec readonly changelog read` | PowerShell: `Get-Content -Raw CHANGELOG.md` in the project directory |

## Step meanings

- **changelog_file**: `CHANGELOG.md` in the project directory, and no other file.
- **place entry**: insert `entry` as one bullet line under the `### <section>` heading inside `## Unreleased`, after that heading's existing bullets. If that heading is missing, add it in the order Added, Changed, Fixed. Change nothing else in the file, and keep the rest of the text byte-identical.
- **entry format**: one bullet line that states the change in the past tense and ends with the pull request number in parentheses, such as `- Added retry on timeout (#123)`.
