# Screen, repair, retry

```contract
inputs:
  design
order:
  verify#table before generate#impl
```

```logic
screen-repair-retry:
  require design exists
    otherwise:
      abort with "A design is required."

  exec assurance table check from checks as screen
  verify #table design has an assurance table from screen
    otherwise:
      apply assurance screen with design as design
      exec assurance table check from checks as screen
      retry

  generate #impl implementation from design as implementation

  return implementation as implementation
```

## Step meanings

- **assurance screen**: answer the risk questions and add the raised disciplines' checks to the design as an assurance table.
