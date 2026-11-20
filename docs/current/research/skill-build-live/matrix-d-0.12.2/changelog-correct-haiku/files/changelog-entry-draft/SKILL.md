---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added, Changed or Fixed, ending with the pull request number in parentheses. Use when asked to record a change in the changelog.
---

# Changelog entry

Adds exactly one entry to `CHANGELOG.md`. Nothing else is edited.

```contract
inputs:
  request, changelog_file
order:
  verify #loaded the changelog text is present from current before generate entry
  ask user to approve the entry before write updated_changelog
```

```logic
changelog-entry:
  require request exists
    otherwise:
      abort with "Describe the change to record in CHANGELOG.md."

  read changelog from changelog_file as current
  verify #loaded the changelog text is present from current
    otherwise:
      abort with "CHANGELOG.md was not found in the project root; nothing was written."

  if request does not give a pull request number:
    ask user for the pull request number as pr_number
    verify #pr_given pr_number is a pull request number such as 123 from pr_number
      otherwise:
        abort with "No pull request number given; nothing was written."
  else:
    generate pr_number from request as pr_number

  if request does not make clear whether the change is Added, Changed or Fixed:
    ask user for the section as section
    verify #section_given section is Added, Changed or Fixed from section
      otherwise:
        abort with "No section chosen; nothing was written."
  else:
    generate section from request as section

  generate entry from request, current, pr_number, section as entry
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; CHANGELOG.md was not changed."

  apply changelog placement with entry as updated_changelog
  write updated_changelog with changelog_file
  return updated_changelog as changelog
```

## Step meanings

- **changelog placement**: insert the approved entry into the current `CHANGELOG.md` text (already read as `current`) under the `### <section>` heading inside `## Unreleased`. Add that heading if it is missing, keeping the order Added, Changed, Fixed. Change nothing else in the file.
- **entry**: one bullet line in the same style as the existing bullets in `CHANGELOG.md`, describing the change, and ending with the pull request number in parentheses, such as `(#123)`.
- **changelog_file**: `CHANGELOG.md` in the project root. No other file is read for writing or changed.
