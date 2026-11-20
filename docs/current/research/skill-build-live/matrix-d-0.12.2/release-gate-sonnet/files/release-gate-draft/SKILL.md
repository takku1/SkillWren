---
name: release-gate
description: Gate a release tag behind a passing test suite and an explicit version confirmation, then create a local git tag. Never pushes to any remote. Use when asked to tag, cut or prepare a release.
---

# Release gate

```contract
inputs:
  request
order:
  verify #tests before ask user to confirm the version
  ask user to confirm the version before exec git tag
```

```logic
release-gate:
  ask user for the test command as test_command

  exec test suite from repository as tests
  verify #tests every test passed and the command exited successfully from tests
    otherwise:
      abort with "Tests failed. Nothing was tagged and nothing was pushed."

  ask user for the version number as version
  show version
  ask user to confirm the version number
  require user confirms the version number
    otherwise:
      abort with "Version not confirmed. Nothing was tagged and nothing was pushed."

  exec git tag from repository as tag_status
  verify the tag was created locally from tag_status
    otherwise:
      abort with "The tag could not be created. Nothing was pushed."

  return #tagged:
    version
    tag_status
```

| Step | Command |
|---|---|
| `exec test suite` | the `test_command` the user gave, run in the repository root |
| `exec git tag` | `git tag <version>` (local only) |

## Step meanings

- **repository**: the git repository in the current working directory.
- **Never push**: this skill runs no `git push`, no `--follow-tags`, and nothing that contacts a remote. Pushing is left to the user.
