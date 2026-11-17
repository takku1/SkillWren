# Batch 5 flows

```contract
order:
  ask#approve before verify#ready
  verify#ready before write#shipment
```

```logic
f21ingest:
  read request as request
  return request as request
```

```logic
f21store:
  require record exists
    otherwise:
      abort with "A record is required."
  write record with records
  return record as record
```

```logic
f22:
  verify service is healthy
    otherwise:
      exec restart from service as restarted
      verify service is healthy
        otherwise:
          exec reload from service as reloaded
          verify service is healthy
            otherwise:
              abort with "Service is still unhealthy after restart and reload."
  read service state as state
  return state as state
```

```logic
f23:
  ask operator to approve note
  require confirmation
    otherwise:
      abort with "The note was not approved."
  write note with notes
  return note as note
```

```logic
f24:
  write note with notes
  return note as note
```

```logic
f25:
  ask #approve lead to approve shipment
  require confirmation
    otherwise:
      abort with "The shipment was not approved."
  exec goods check from checks as results
  verify #ready goods are ready from results
    otherwise:
      abort with "The goods are not ready."
  write #shipment shipment with shipments
  return shipment as shipment
```
