# Correlated branches are not assumed

The second branch repeats the first branch's condition but is not nested in
it, so `integration` is unbound when the subject is unknown.

```logic
design:
  generate scope from request as scope
  if subject is known:
    read integration guide from references/existing.md as integration
  if subject has existing contracts:
    apply delta with integration as scope
  return scope as scope
```

## Step meanings

- **delta**: describe the change against existing contracts.
