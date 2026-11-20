# Design flow

```logic
design:
  require request exists
    otherwise:
      abort with "A request is required."
  generate design from request as design
  return design as design
```
