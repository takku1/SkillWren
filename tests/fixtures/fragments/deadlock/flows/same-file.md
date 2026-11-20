# One flow that writes, then starts the guard

```contract
order:
  never write before exec guard start
```

```logic
build:
  generate design from request as design
  write design with design_docs
  exec guard start from guard as started
  verify guard accepted the run from started
    otherwise:
      abort with "The guard refused to start."
  return design as design
```
