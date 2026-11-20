# Implement flow

The guard refuses to start over edits it did not see.

```contract
order:
  never write before exec guard start
```

```logic
implement:
  exec guard start from guard as started
  verify guard accepted the run from started
    otherwise:
      abort with "The guard refused to start."
  generate implementation from design as implementation
  write implementation with subject
  return implementation as implementation
```
