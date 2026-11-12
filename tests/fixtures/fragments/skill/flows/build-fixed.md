# Build flow (fixed)

The screen is checked on every path, and the check is a command whose exit
status a guard can record, so the rule rests on evidence, not self-report.

```contract
order:
  verify design has an assurance table before write implementation
```

```logic
build:
  require request exists
    otherwise:
      abort with "A request is required."

  unless design is known:
    run design from flows/design.md with:
      request = request

  exec assurance table check from checks as screen
  verify design has an assurance table from screen
    otherwise:
      apply assurance screen with design as design
      write design with design_docs
      exec assurance table check from checks as screen
      retry

  generate implementation from design as implementation
  write implementation with subject
  return implementation as implementation
```

## Step meanings

- **assurance screen**: run the screen and add its table to the design.
