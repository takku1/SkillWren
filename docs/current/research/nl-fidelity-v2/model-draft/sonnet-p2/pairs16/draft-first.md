# Batch 4 flows

```contract
inputs:
  request, fast, draft, slot, report
order:
  verify#window_open before write#book_slot
  apply redaction before write#write_clean
  generate parts before generate assembly
  generate assembly before exec fresh check
  verify#assembly_match before write#write_assembly
```

```logic
f16:
  if fast flag is set:
    apply fast path with request as request
  return request as request

f17:
  exec window check from checks as window_status
  verify #window_open window is open from window_status
    otherwise:
      abort with "The window shut."
  write #book_slot slot with bookings
  return slot as booking

f18:
  apply redaction with draft as clean
  write #write_clean clean with output
  return clean as result

f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec fresh check from checks as check
  verify #assembly_match assembly matches check from check
    otherwise:
      abort with "The assembly does not match the fresh check."
  write #write_assembly assembly with output
  return assembly as result

f20:
  show report
  return report as report
```

## Step meanings

- **fast path**: the shortened handling of the request, taken only when the fast flag is set.
- **redaction**: remove sensitive content from the draft in memory, producing the clean result.
