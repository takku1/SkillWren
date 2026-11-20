---
name: release-gate
description: Gate a release tag behind the test suite and a user-confirmed version number. Use when asked to tag a release, cut a release, or create a version tag. Not for pushing, publishing, or deploying: this skill never pushes to a remote.
---

# Release gate

Creates a local git tag for a release only after the test suite passes and
the user confirms the version number. It never pushes.

```contract
always:
  run the test suite before any tag is created
never:
  push to any remote
  create a tag when a test has failed
  create a tag with a version the user did not confirm
inputs:
  request, repo
order:
  ask user to confirm the version number before exec run test suite
  verify#tests before exec create git tag
  ask user to confirm the version number before exec create git tag
```

```logic
release-gate:
  require request exists
    otherwise:
      abort with "Say which release to tag."

  ask user for the version number as version
  show version
  ask user to confirm the version number
  require user confirms the version number
    otherwise:
      abort with "Version not confirmed. No tag created."

  generate test command from repo as test_command
  if test command is unknown:
    ask user for the test command as test_command
  show test_command

  exec run test suite from repo as tests
  verify #tests the test suite passed from tests
    otherwise:
      abort with "Tests failed. No tag created."

  exec create git tag from repo as tag
  return tag as tag
```

## Commands

| Step | Command |
|---|---|
| `exec run test suite` | the confirmed test command, or the detected one (for example `npm test`, `pytest`, `go test ./...`) |
| `exec create git tag` | `git tag <version>` |

## Step meanings

- **test command**: the repository's test command. Detect it from the
  project files (`package.json`, `pyproject.toml`, `go.mod`, `Makefile`).
  If no single command is clear, the user supplies it.
- **version**: the version string the user typed. It becomes the tag name
  unchanged.
