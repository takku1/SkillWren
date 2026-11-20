# Build flow

A build designs first, keeping the design note, then implements that design.

```logic
build:
  run design from design.md with:
    request = request
  run implement from implement.md with:
    design = design
  return code as code
```
