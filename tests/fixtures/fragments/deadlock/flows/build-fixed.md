# Build flow: design, then implement under the narrowed rule

```logic
build:
  run design from flows/design.md with:
    request = request
  run implement from flows/implement-narrow.md with:
    design = design
  return implementation as implementation
```
