# Build flow

A build designs first, keeping the design note, then implements.

```logic
build:
  run design from flows/design.md with:
    request = request
  run implement from flows/implement.md with:
    design = design
  return code as code
```
