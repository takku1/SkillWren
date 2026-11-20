# Implement flow

The guard refuses to start over code edits it did not see. Design notes
do not count; code does.

```contract
order:
  exec#guard before write#code
  never write#code before exec#guard
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
