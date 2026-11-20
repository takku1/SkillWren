# Implement flow

The guard refuses to start over any edit it did not see.

```contract
order:
  never write before exec#guard
```

```logic
implement:
  exec #guard guard start from guard as started
  verify the guard accepted the run from started
    otherwise:
      abort with "The guard refused to start."
  generate code from design as code
  write #code code with subject
  return code as code
```
