# Screen, repair, retry

```contract
inputs:
  design
order:
  verify#table before generate implementation
```

```logic
screen-and-implement:
  verify #table design has an assurance table
    otherwise:
      apply assurance screen with design as design
      retry

  generate implementation from design as implementation
  return implementation as implementation
```

## Step meanings

- **assurance screen**: add the missing assurance table to the design and return the updated design.
