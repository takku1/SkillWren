# Build flow

A build designs first, keeping the design note, then implements from that design.

```logic
build:
  require request exists
    otherwise:
      abort with "A request is required."
  run design from flows/design.md with:
    request: request
  run implement from flows/implement.md with:
    design: design
    subject: subject
  return code as code
```
