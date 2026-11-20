# Stack flow

Use when any layer needs a technology chosen or reopened, including a
choice between standard-library options.

```contract
order:
  exec#stack-profiles before return#choice
```

```logic
stack:
  exec #stack-profiles stack profiles from stack_tool as profiles
  verify the candidates are compared from profiles
    otherwise:
      abort with "No candidate comparison."
  generate choice from profiles as choice
  return #choice choice as choice
```
