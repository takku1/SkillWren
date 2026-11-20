---
name: release-gate
description: Gate a release tag. Runs the test suite, stops if any test fails, asks the user to confirm the version number, then creates a local git tag. Never pushes to a remote. Use when asked to tag, cut, or release a version.
---

# Release gate

Creates a local git tag for a release only after the tests pass and the user
confirms the version number. This skill never pushes anything to a remote.

```contract
inputs:
  request
order:
  exec test suite before ask user to confirm the version number
  ask user to confirm the version number before exec git tag
```

```logic
release-gate:
  require repository is a git repository
    otherwise:
      abort with "No git repository here. Open the repository, then run this again. No tag was created."

  ask user for the test command as test_command
  exec test suite from repository as test_result

  verify every test passed from test_result
    otherwise:
      abort with "Tests failed. No version was asked for and no tag was created."

  ask user for the version number as version
  show version
  ask user to confirm the version number
  require user confirms the version number
    otherwise:
      abort with "Version not confirmed. No tag was created."

  exec git tag from repository as tag_result
  verify the tag was created from tag_result
    otherwise:
      abort with "git tag failed; see the output above. Nothing was pushed."

  return tag_result as tag
```

| Step | Command |
|---|---|
| `exec test suite` | the `test_command` the user gave, run from the repository root |
| `exec git tag` | `git tag <version>` (a lightweight tag on the current commit) |

## Step meanings

- **repository**: the git repository in the current working directory.
- **test command**: the command that runs the project's full test suite, as
  the user gave it. Do not guess one.
- **version number**: the release version exactly as the user typed it. Do
  not invent or adjust it.

Rules that hold throughout:

- Never run `git push`, or any command that sends data to a remote.
- If a test fails, stop at once. Do not retry the suite to get a pass.
