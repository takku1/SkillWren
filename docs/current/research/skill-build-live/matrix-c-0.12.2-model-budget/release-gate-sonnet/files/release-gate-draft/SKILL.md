---
name: release-gate
description: Gate a release tag behind a passing test suite and an explicit version confirmation, then create a local git tag. Never pushes. Use before tagging a release.
---

# Release gate

```contract
inputs:
  request, test_command
order:
  verify #tests before ask user to confirm the version
  ask user to confirm the version before exec git tag
  verify #tests before exec git tag
```

```logic
release-gate:
  require test_command exists
    otherwise:
      abort with "No test command given; nothing was tagged."

  exec test suite from tools as tests
  verify #tests every test passed from tests
    otherwise:
      abort with "Tests failed; refusing to continue. Nothing was tagged."

  apply version proposal with request as version
  show version
  ask user to confirm the version
  require user confirms the version
    otherwise:
      abort with "Version not confirmed; nothing was tagged."

  exec git tag from tools as tag
  verify the tag was created locally from tag
    otherwise:
      abort with "Tag creation failed; nothing was pushed."

  return #tagged:
    tag = version
```

| Step | Command |
|---|---|
| `exec test suite` | the `test_command`, run in the repository root |
| `exec git tag` | `git tag -a <version> -m "Release <version>"` (local only) |

## Step meanings

- **version proposal**: take the version from the request, or the next version after the latest local tag; it is only a proposal until the user confirms.
- **tools**: the repository's command line. Only local commands are allowed. Never run `git push`, `git push --tags`, or any command that writes to a remote.
