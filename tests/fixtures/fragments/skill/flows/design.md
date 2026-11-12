# Design flow

Load for design work. The block is ordered instructions.

```logic
design:
  require request exists
    otherwise:
      abort with "A request is required."

  generate scope from request as scope
  apply assurance screen with scope as scope
  generate design from scope as design

  if design should stay in chat:
    return design as design

  write design with design_docs
  return design as design
```

## Step meanings

- **assurance screen**: answer the risk questions and record raised disciplines.

An example that is not logic:

```sh
python3 scripts/run_guard.py start --write-set "src/a b.py"
```
