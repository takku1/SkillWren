# Batch 4: branches, apply, chains, advisory verbs

```contract
order:
  verify#parts before write#assembly
```

Take the fast path only when the flag is set.

```logic
f16:
  require request exists
    otherwise:
      abort with "No request."
  if fast flag is set:
    write #fast fast result with target
  return request as request
```

Wait for the window before acting.

```logic
f17:
  require request exists
    otherwise:
      abort with "No request."
  when window is open:
    verify #window window is open
      otherwise:
        abort with "Window shut."
    write #slot booked slot with target
  return request as request
```

Apply a named transform, then keep the result.

```logic
f18:
  require draft exists
    otherwise:
      abort with "No draft."
  apply redaction with draft as clean
  write #clean redacted draft with target
  return clean as clean
```

## Step meanings

- **redaction**: remove secrets from the draft in memory.

A generation chain feeding one write.

```logic
f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec assembly check from checks as report
  verify #parts assembly matches parts from report
    otherwise:
      abort with "Mismatch."
  write #assembly finished assembly with target
  return assembly as assembly
```

Show the report without enforcing anything.

```logic
f20:
  exec audit check from checks as report
  show report to requester
  return report as report
```
