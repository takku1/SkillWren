# Build flow

The implement flow's guard refuses to start over any earlier write, and the design
flow writes the design note. Implement therefore runs first, on a draft design, and
the design flow runs after it to write the note.

```logic
build:
  generate draft design from request as draft
  run implement from flows/implement.md with:
    design = draft
  run design from flows/design.md with:
    request = request
  return code as code
```
