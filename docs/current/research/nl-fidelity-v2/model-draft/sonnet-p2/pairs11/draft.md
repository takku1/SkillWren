# Batch 3 flows

```contract
inputs:
  access_key, holder, source, destination, items, request
order:
  ask#approve_rotation before write#rotate_key
```

```logic
f11:
  ask #approve_rotation holder to approve access key rotation
  require confirmation
    otherwise:
      abort with "The holder refused the rotation."
  write #rotate_key access_key with access_key
  return access_key as access_key
```

```logic
f12:
  exec audit check from checks as report
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
  write #write_copy source with destination
  return destination as destination
```

```logic
f14:
  for each items as item:
    apply processing with item as processed
    write #write_item processed with processed_items
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

- **processing**: process one item as the task defines; the item itself is not modified in place.
