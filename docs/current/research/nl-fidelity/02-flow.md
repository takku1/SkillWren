# Approval-gated release

A human approves, confirmation is required, and only then the bundle
is written.

```contract
order:
  ask#approval before write#release
```

```logic
release:
  ask #approval user to approve production deploy
  require confirmation
    otherwise:
      abort with "No approval."
  write #release production bundle with target
  return bundle as bundle
```
