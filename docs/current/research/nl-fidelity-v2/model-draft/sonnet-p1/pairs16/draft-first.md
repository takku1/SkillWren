# Batch 4 flows

```contract
order:
  verify#window before write#slot
  apply redaction before write#clean
  generate assembly before exec fresh check
  verify#match before write#assembled
```

```logic
f16:
  if fast flag is set:
    apply fast path with request as request
  return request as request
```

```logic
f17:
  verify #window window is open
    otherwise:
      abort with "The window has shut."
  write #slot slot with booking
  return
```

```logic
f18:
  apply redaction with draft as clean
  write #clean clean with destination
  return
```

```logic
f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec fresh check from checks as check
  verify #match assembly matches fresh check from check
    otherwise:
      discard assembly
      abort with "Assembly does not match the fresh check."
  write #assembled assembly with target
  return
```

```logic
f20:
  show audit report
  return
```

## Step meanings

- **fast path**: the shortened route for the request, taken only when the fast flag is set.
- **redaction**: remove sensitive content from the draft, in memory, producing the clean result.
