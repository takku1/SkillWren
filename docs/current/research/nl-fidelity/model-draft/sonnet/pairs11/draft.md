# Batch 3 flows

```contract
order:
  ask#approval before write#rotation
```

```logic
f11:
  ask #approval holder to approve key rotation
  require confirmation
    otherwise:
      abort with "Key rotation was refused."
  write #rotation rotated_key with access_key
  return rotated_key as rotated_key
```

```logic
f12:
  read audit check as report
    otherwise:
      abort with "The audit check could not be observed."
  return report as report
```

```logic
f13:
  require source exists
  require destination exists
  write source with destination
  return source as copy
```

```logic
f14:
  for each items as item:
    apply process with item as processed
    write processed with processed_items
  return items as items
```

```logic
f15:
  require request exists
    otherwise:
      abort with "A request is required."
  return:
    request = request
```

## Step meanings

- **process**: transform the item as the request for this flow defines; the intent gives no further detail.
