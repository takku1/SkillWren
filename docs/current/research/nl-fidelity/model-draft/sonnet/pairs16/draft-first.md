# Batch 4 flows

```contract
inputs:
  request, fast, window, slot, draft, request, audit_report
order:
  verify#window before write#book
  apply redaction before write clean
  generate parts before generate assembly
  verify#match before write#out
```

```logic
f16:
  if fast flag is set:
    apply fast path with request as fast_result
  return request as request
```

```logic
f17:
  verify #window window is open
    otherwise:
      abort with "The window shut."
  write #book slot with bookings
```

```logic
f18:
  apply redaction with draft as clean
  write clean with output
```

```logic
f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec fresh check from checks as check
  verify #match assembly matches check from check
    otherwise:
      discard assembly
      abort with "Assembly does not match the fresh check."
  write #out assembly with output
```

```logic
f20:
  show audit_report
```

## Step meanings

- **fast path**: the fast-path handling of the request, performed only when the fast flag is set.
- **redaction**: redact the draft in memory, producing the clean result before anything is written.
