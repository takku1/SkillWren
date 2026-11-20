# Build flow

A build designs, keeping its design note, then implements.

```logic
build:
  run design from flows/design.md with:
    request = request
  run implement from flows/implement.md with:
    design = design
  write #notes design with design_docs
  return code as code
```
