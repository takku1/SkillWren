# Implement flow, rule narrowed to code writes

Design notes stay writable; only code written before the guard starts
would make the declaration late.

```contract
order:
  never write implementation before exec guard start
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
