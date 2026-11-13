# Batch 5: two flows, repair, unruled, unverified, full chain

```contract
order:
  verify#final before write#shipment
```

Two small flows in one file: one reads, one writes.

```logic
f21ingest:
  require request exists
    otherwise:
      abort with "Nothing."
  return request as request
```

```logic
f21store:
  require record exists
    otherwise:
      abort with "Nothing."
  write #record incoming record with target
  return record as record
```

Two-step repair before giving up.

```logic
f22:
  exec service check from checks as state
  verify #service service is healthy from state
    otherwise:
      apply service restart with state as state
      apply service reload with state as state
      abort with "Still unhealthy."
  return state as state
```

## Step meanings

- **service restart**: restart the service in memory.
- **service reload**: reload the service configuration.

Ask, then write, with no ordering rule at all.

```logic
f23:
  ask operator to approve the note
  require confirmation
    otherwise:
      abort with "Not approved."
  write #note approved note with target
  return note as note
```

A typed write with no verification step anywhere.

```logic
f24:
  require note exists
    otherwise:
      abort with "No note."
  write #memo recorded note with target
  return note as note
```

Ask, confirm, check, verify, write.

```logic
f25:
  ask #lead operator to approve shipment
  require confirmation
    otherwise:
      abort with "Shipment refused."
  exec final check from checks as state
  verify #final shipment is ready from state
    otherwise:
      abort with "Not ready."
  write #shipment approved shipment with target
  return shipment as shipment
```
