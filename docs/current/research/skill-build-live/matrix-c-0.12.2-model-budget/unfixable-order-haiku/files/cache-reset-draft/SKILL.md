---
name: cache-reset
description: Delete the build cache by running make clean, then ask the user whether to rebuild now. Use when asked to reset, clear or clean the build cache.
---

# cache-reset

```contract
inputs:
  request
order:
  exec clean before ask user to decide whether to rebuild
```

```logic
cache-reset:
  exec clean from project as cleaned
  verify #cleaned the clean command exited with status 0 from cleaned
    otherwise:
      abort with "make clean failed; the build cache may be partly deleted. Nothing was rebuilt."

  ask user to decide whether to rebuild now
  require user decides whether to rebuild now
    otherwise:
      return #kept as result
  return #rebuild as result
```

| Step | Command |
|---|---|
| `exec clean` | `make clean` |

## Step meanings

- **project**: the current working directory, which holds the Makefile. `make clean` deletes files here; it is not read-only.
