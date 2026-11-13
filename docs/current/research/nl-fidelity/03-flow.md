# Screen, repair, retry, then implement

The table check repeats until the design carries the table; only then
does implementation start.

```contract
order:
  verify#table before write#implementation
```

```logic
develop:
  require design exists
    otherwise:
      abort with "No design."
  exec table check from checks as screen
  verify #table design has an assurance table from screen
    otherwise:
      apply assurance screen with design as design
      exec table check from checks as screen
      verify #recheck design has an assurance table from screen
      retry
  generate implementation from design as implementation
  write #implementation implementation with subject
  return implementation as implementation
```

## Step meanings

- **assurance screen**: run the screen and add its table to the design.
