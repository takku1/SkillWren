# Build flow (gap)

The design step is skipped when a design is supplied, so the screen can be
skipped too: the shape of field report 3, finding G1.

```contract
order:
  apply assurance screen before write implementation
```

```logic
build:
  require request exists
    otherwise:
      abort with "A request is required."

  unless design is known:
    run design from flows/design.md with:
      request = request

  generate implementation from design as implementation
  write implementation with subject
  return implementation as implementation
```
