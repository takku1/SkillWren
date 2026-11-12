# Build flow (always designs)

```contract
order:
  apply assurance screen before write implementation
```

```logic
build:
  run design from flows/design.md with:
    request = request
  generate implementation from design as implementation
  write implementation with subject
  return implementation as implementation
```
