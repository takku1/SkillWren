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
```

```logic
cache-reset:
  exec make clean from shell as cleaned
  verify #cleaned make clean finished without errors from cleaned
    otherwise:
      abort with "make clean failed; the cache may be partly deleted and no rebuild was offered."

  ask user to rebuild now
  require user wants to rebuild now
    otherwise:
      return cleaned as result

  exec make rebuild from shell as rebuilt
  verify the rebuild finished without errors from rebuilt
    otherwise:
      abort with "The rebuild failed."

  return rebuilt as result
```

| Step | Command |
|---|---|
| `exec make clean` | `make clean` (deletes files; not read-only) |
| `exec make rebuild` | `make` |

## Step meanings

- **shell**: the project's command line, run in the project root.
