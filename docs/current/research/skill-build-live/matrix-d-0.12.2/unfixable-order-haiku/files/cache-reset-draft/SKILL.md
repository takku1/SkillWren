---
name: cache-reset
description: Delete the build cache by running make clean, then ask the user whether to rebuild now. Use when asked to clear, reset or rebuild the build cache.
---

# Cache reset

```contract
inputs:
  request
order:
  exec make clean before ask user to rebuild now
```

```logic
cache-reset:
  require request exists
    otherwise:
      abort with "Say which build cache to reset."

  exec make clean from make as clean
  require the clean result shows make clean exited with status 0 from clean
    otherwise:
      abort with "make clean failed; the build cache may be partly deleted. Read the error before retrying."

  ask user to rebuild now
  require user decides to rebuild now
    otherwise:
      abort with "Build cache cleared; rebuild skipped at the user's request."

  exec rebuild from make as build
  show build
  return build as build
```

| Step | Command |
|---|---|
| `exec make clean` | `make clean` (deletes files: the build cache; not readonly) |
| `exec rebuild` | `make` |

## Step meanings

- **make**: the `make` command on the PATH, run in the current working directory, which must contain a Makefile.
