# Batch 3 flows

```contract
inputs:
  key, source, destination, items, item_store, request
```

```logic
f11:
  ask #approval key holder to approve access key rotation
  require confirmation
    otherwise:
      abort with "Rotation refused by the key holder."
  write #rotation key with key
  return key as key
```

```logic
f12:
  exec readonly audit check from checks as report
  return report as report
```

```logic
f13:
  require source exists
    otherwise:
      abort with "The source is required."
  require destination exists
    otherwise:
      abort with "The destination is required."
  write #copy source with destination
  return destination as destination
```

```logic
f14:
  for each items as item:
    apply processing with item as processed
    write processed with item_store
  return items as items
```

```logic
f15:
  require request exists
    otherwise:
      abort with "A request is required."
  return:
    request
```

## Step meanings

- **processing**: process one item and bind the processed result; the item itself is not modified.
