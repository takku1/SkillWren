---
name: cache-reset
description: Delete the build cache with make clean, then ask whether to rebuild now. Use when asked to reset, clear or clean the build cache.
---

# Cache reset

```contract
inputs:
  request
order:
  verify #cleaned before ask user to rebuild now
  exec make clean before ask user to rebuild now
```

```logic
cache-reset:
  exec make clean from project as cleaned
  verify #cleaned make clean finished without errors from cleaned
    otherwise:
      abort with "make clean failed; the cache may be partly deleted and no rebuild was offered."

  ask user to rebuild now
  require user wants to rebuild now
    otherwise:
      return cleaned as result

  exec make from project as rebuilt
  verify the rebuild finished without errors from rebuilt
    otherwise:
      abort with "make failed after the clean."

  return rebuilt as result
```

| Step | Command |
|---|---|
| `exec make clean` | `make clean` (deletes the build cache files; not read-only) |
| `exec make` | `make` |

## Step meanings

- **project**: the project directory containing the Makefile.
