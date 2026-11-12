# Declared inputs make U1 strict

```contract
inputs:
  request
```

```logic
build:
  generate plan from request and design as plan
  apply review with design as plan
  return plan as plan
```

## Step meanings

- **review**: compare the plan with the design.
