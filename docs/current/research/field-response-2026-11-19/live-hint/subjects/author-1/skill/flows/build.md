# Build flow

A build designs, keeping its design note, then implements.

```logic
build:
  run design from design.md with:
    request = request
  run implement from implement.md with:
    design = design
  write #notes design with design_docs
  return design as design
```
