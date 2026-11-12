# A mutating callee before an ask breaks dismissal safety

```logic
build:
  run design from flows/design.md with:
    request = request
  ask user to approve the design
  require confirmation
    otherwise:
      abort with "Declined."
  return design as design
```
