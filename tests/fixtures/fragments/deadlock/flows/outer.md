# Outer flow: the conflicting rule is two runs down

```logic
build:
  run design from flows/design.md with:
    request = request
  run wrapped from flows/wrapper.md with:
    design = design
  return implementation as implementation
```
