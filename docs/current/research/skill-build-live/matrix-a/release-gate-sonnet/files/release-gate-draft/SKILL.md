---
name: release-gate
description: Gate a release tag behind a passing test suite and an explicit version confirmation, then create a local git tag. Never pushes to a remote. Use when asked to tag, cut or gate a release.
---

# Release gate

```contract
inputs:
  project
order:
  verify #tests before ask user to confirm the version number
  ask user to confirm the version number before exec git tag
```

```logic
release-gate:
  generate test command from project as test_command
  unless the test command was found in the project:
    ask user for the test command as test_command
  show test_command

  exec readonly test suite from test_command as results
  verify #tests every test passed and the suite exited with code 0 from results
    otherwise:
      abort with "Tests failed; no tag was created."

  generate proposed version from project as proposed
  show proposed
  ask user to confirm the version number
  require user confirms the version number
    otherwise:
      abort with "Version not confirmed; no tag was created."

  exec git tag from git as tag
  generate local-only note from tag as note
  return #tagged:
    tag
    note
```

| Step | Command |
|---|---|
| `exec readonly test suite` | the test command bound to `test_command`, run from the repository root |
| `exec git tag` | `git tag -a v<version> -m "Release v<version>"` on the current HEAD, using the confirmed version |

## Step meanings

- **project**: the current repository. **git**: its local git command line.
- **test command**: found from the project (`package.json` scripts, `pytest`, `Makefile`, etc.); never guessed. If none is found, the user supplies it.
- **proposed version**: the next version inferred from the latest tag and project metadata, as a bare number such as `1.4.0`.
- **local-only note**: tell the user the tag exists only locally and that pushing is theirs to do.
- **Never push**: this skill never runs `git push`, never pushes the tag, and never contacts a remote.
