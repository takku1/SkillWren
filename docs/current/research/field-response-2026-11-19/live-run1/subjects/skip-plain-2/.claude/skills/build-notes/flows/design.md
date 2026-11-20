# Design flow

```logic
design:
  require request exists
    otherwise:
      abort with "A request is required."
  generate design from request as design
  if the design is worth keeping:
    write #notes design with design_docs
  return design as design
```

A design note goes in `docs/` and is optional.
