---
name: changelog-entry
description: Add one entry to CHANGELOG.md for a change the user describes, under Added, Fixed, or Changed, ending with the pull request number in parentheses. Use when asked to add, record, or write a changelog entry.
---

# Changelog entry

Adds one entry to `CHANGELOG.md` and nothing else. Shows the entry to the
user and writes only after approval.

```contract
inputs:
  request
order:
  ask user to approve the entry before write updated
```

```logic
changelog-entry:
  require request exists
    otherwise:
      abort with "Describe the change to add to the changelog."

  read changelog from changelog_file as changelog
    otherwise:
      ask user to say whether to create CHANGELOG.md
      require user says to create CHANGELOG.md
        otherwise:
          abort with "CHANGELOG.md was not created; nothing was written."
      generate starting changelog from request as changelog
      return to drafting

  label drafting:
  generate pull request number from request as prnumber
  require the pull request number in prnumber is a positive whole number
    otherwise:
      ask user for the pull request number as prnumber
      retry

  if request does not clearly say Added, Fixed, or Changed:
    ask user for the section as section
  else:
    generate section from request as section

  require section is Added, Fixed, or Changed
    otherwise:
      ask user for the section as section
      retry

  generate entry from request, section, prnumber as entry
  apply house style with changelog as entry

  verify #suffix the entry ends with (#prnumber) from entry
    otherwise:
      apply pr suffix with entry as entry
      retry

  show section
  show prnumber
  show entry
  ask user to approve the entry
  require user approves the entry
    otherwise:
      abort with "Entry not approved; nothing was written."

  generate updated changelog from changelog, section, entry as updated
  write updated with changelog_file

  return #written:
    entry = entry
```

## Step meanings

- **house style**: match the bullet style and any heading layout already used in `changelog` under the section. If the file has no existing entries, use a plain `- ` bullet in past tense.
- **pr suffix**: append ` (#N)` to the end of the entry, where N is the pull request number in `prnumber`.
- **changelog_file**: `CHANGELOG.md` in the working directory. It is the only file this skill writes.
- **Unreleased**: if `changelog` has no `## Unreleased` section, add one above the first released version before placing the entry.
- **Keep a Changelog style**: when `changelog` is empty or new, use `### Added`, `### Fixed`, and `### Changed` headings, one bullet per change.
