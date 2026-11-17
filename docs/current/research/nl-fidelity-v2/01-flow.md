# Guarded config write

Verify the candidate, abort on failure, and write only verified content.

```contract
order:
  verify#check before write#config
```

```logic
deploy:
  exec config check from checks as result
  verify #check candidate has debug off from result
    otherwise:
      abort with "Unverified config."
  write #config candidate with target
  return candidate as candidate
```
