---
name: release-gate
description: Gate a release tag behind a passing test suite and an explicit version confirmation. Use when asked to tag a release. Creates a local git tag only; never pushes to a remote.
---

# Release gate

```contract
inputs:
  request
order:
  verify #tests before ask user to confirm the version
  ask user to confirm the version before write release tag
```

```logic
release-gate:
  require request exists
    otherwise:
      abort with "Say which release to tag."

  exec readonly git status porcelain from repo as status
  verify #clean the working tree has no uncommitted changes from status
    otherwise:
      abort with "Uncommitted changes present. Commit or stash them, then run again. Nothing was tagged."

  exec test suite from repo as tests
  verify #tests the test suite exited with status zero from tests
    otherwise:
      abort with "Tests failed. No version was asked for and no tag was created."

  ask user for the version as version
  require version is a semantic version of the form vX.Y.Z
    otherwise:
      abort with "The version must look like vX.Y.Z. Nothing was tagged."

  exec readonly git tag list from repo as existing_tags
  verify #new the tag named by version does not appear in the tag list from existing_tags
    otherwise:
      abort with "That tag already exists. Nothing was changed."

  ask user to confirm the version
  require user confirms the version
    otherwise:
      abort with "Version not confirmed. No tag was created."

  write release tag with repo
  return version as tag_name
```

| Step | Command |
|---|---|
| `exec readonly git status porcelain` | `git status --porcelain` |
| `exec test suite` | the repository's test command: the `test` script in `package.json`, or the `pytest` or `make test` entry point; if none is declared, ask the user for it before running anything |
| `exec readonly git tag list` | `git tag --list` |
| `write release tag` | `git tag -a <version> -m "Release <version>"` (local only) |

This skill never runs `git push` or any other command that contacts a remote.
