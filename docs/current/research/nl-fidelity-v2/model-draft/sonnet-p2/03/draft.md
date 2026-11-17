```contract
inputs:
  design
```

```logic
screen-repair-retry:
  exec assurance table check from checks as screen
  verify #table design has an assurance table from screen
    otherwise:
      apply assurance screen with design as design
      exec assurance table check from checks as screen
      verify #table_recheck design has an assurance table from screen
      retry

  generate implementation from design as implementation
  return implementation as implementation
```

## Step meanings

- **assurance screen**: add the missing assurance table to the design.
