# Batch 3: rotation, evidence, gates, loop, block return

```contract
order:
  ask#holder before write#key
```

Rotate a key only after the holder approves it.

```logic
f11:
  ask #holder key holder to approve rotation
  require confirmation
    otherwise:
      abort with "Rotation refused."
  write #key fresh key with target
  return key as key
```

Evidence observed and returned, nothing written.

```logic
f12:
  exec audit check from checks as report
  return report as report
```

Two required inputs before any work.

```logic
f13:
  require source exists
    otherwise:
      abort with "No source."
  require destination exists
    otherwise:
      abort with "No destination."
  write #copy source content with target
  return copy as copy
```

Handle every item in turn.

```logic
f14:
  require items exist
    otherwise:
      abort with "No items."
  for each items as item:
    write #item processed item with target
  return items as items
```

Return block form.

```logic
f15:
  require request exists
    otherwise:
      abort with "Nothing."
  return:
    notes = request
```
