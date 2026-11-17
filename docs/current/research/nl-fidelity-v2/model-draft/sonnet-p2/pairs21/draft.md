# Batch 5 flows

```contract
inputs:
  request, record, note, goods
order:
  verify#ready before write#shipwrite
```

```logic
f21ingest:
  read request as body
  return body as request
```

```logic
f21store:
  require record exists
    otherwise:
      abort with "A record is required."

  write #storewrite record with store
  return record as record
```

```logic
f22:
  exec health check from checks as health
  verify #healthy service is healthy from health
    otherwise:
      exec restart service from checks
      exec health check from checks as health
      verify #restarted service is healthy from health
        otherwise:
          exec reload service from checks
          exec health check from checks as health
          verify #reloaded service is healthy from health
            otherwise:
              abort with "Service is still unhealthy after restart and reload."
          return health as state
      return health as state

  return health as state
```

```logic
f23:
  ask operator to approve note
  require confirmation
    otherwise:
      abort with "The note was not approved."

  write #notewrite note with notes
  return note as note
```

```logic
f24:
  write #recordwrite note with notes
  return note as note
```

```logic
f25:
  ask lead to approve shipment
  require confirmation
    otherwise:
      abort with "The shipment was not approved."

  exec readiness check from checks as readiness
  verify #ready goods are ready from readiness
    otherwise:
      abort with "Goods are not ready to ship."

  write #shipwrite goods with shipments
  return goods as shipment
```
