---
name: release-gate
description: Gate a release tag behind a passing test suite and an explicit version confirmation. Use when asked to tag a release, cut a version, or create a release tag in a git repository. Creates a local annotated tag only and never pushes to a remote; not for pushing, publishing, or deploying.
---

# Release gate

```contract
never:
  push to any remote, including git push --tags
  create a tag before the test suite has exited with status 0
  create a tag before the user has confirmed the version number
inputs:
  request
order:
  ask user to confirm the version number before exec project tests
  verify #tests before exec create tag
  ask user to confirm the version number before exec create tag
```

```logic
release-gate:
  require request exists
    otherwise:
      abort with "Say which release to tag."

  require the working directory is a git repository
    otherwise:
      abort with "Not a git repository; no tag was created."

  exec readonly latest tag from repo as latest
  generate proposed version from latest as proposal
  show proposal
  ask user to confirm the version number
  require user confirms the version number
    otherwise:
      abort with "Version not confirmed; no tag was created."

  if no test command can be detected from the project:
    ask user for the test command as test_command
    show test_command

  exec project tests from repo as tests
  verify #tests the test suite exited with status 0 from tests
    otherwise:
      abort with "Tests failed; no tag was created. Fix the failing tests and run the gate again."

  exec create tag from repo as tag
  return tag as release
```

## Commands

| Step | Command |
|---|---|
| `exec readonly latest tag from repo` | `git describe --tags --abbrev=0` (if the repository has no tag yet, the proposal is `0.1.0`) |
| `exec project tests from repo` | the project's test command: detected from its manifest (`package.json` `test` script, `pytest`, `go test ./...`, `cargo test`), or the command the user gave as `test_command` |
| `exec create tag from repo` | `git tag -a v<version> -m "Release v<version>"` (local only; never `git push`) |

## Step meanings

- **repo**: the git repository in the working directory.
- **proposal**: the next version after `latest`, as `MAJOR.MINOR.PATCH`. Patch-bump by default; the user may change it at the confirmation step by rerunning the gate.
- **version**: the confirmed proposal, without the `v` prefix.
