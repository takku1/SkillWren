# Build flow

A build designs first, then implements from that design, and only then keeps
the design note. The design note is written after the implement flow, because
its write would otherwise run before the implement flow's guard.

```logic
build:
  require request exists
    otherwise:
      abort with "A request is required."
  generate design from request as design
  run implement from flows/implement.md with:
    design = design
  write #notes design with design_docs
  return code as code
```
