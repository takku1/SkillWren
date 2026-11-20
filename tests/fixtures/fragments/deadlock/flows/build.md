# Build flow: design, then implement

```logic
build:
  run design from flows/design.md with:
    request = request
  run implement from flows/implement.md with:
    design = design
  return implementation as implementation
```
