# Build flow

Runs the design flow, keeping its design note, then the implement flow, so one build both designs and implements.

```logic
build:
  require request exists
    otherwise:
      abort with "A request is required."
  require subject exists
    otherwise:
      abort with "A subject is required."
  run design from design.md with:
    request = request
  run implement from implement.md with:
    design = design
    subject = subject
  return:
    design = design
    code = code
```
