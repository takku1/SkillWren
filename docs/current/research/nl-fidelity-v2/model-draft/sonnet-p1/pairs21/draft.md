# Batch 5 flows

```contract
order:
  ask#approve before write#ship
  verify#ready before write#ship
```

```logic
f21ingest:
  read the request as request
  return request as request
```

```logic
f21store:
  require record exists
    otherwise:
      abort with "A record is required."
  write record with store
  return record as record
```

```logic
f22:
  exec check service health from service as health
  verify service is healthy from health
    otherwise:
      exec restart service from service
      exec check service health from service as health
      verify service is healthy from health
        otherwise:
          exec reload service from service
          exec check service health from service as health
          verify service is healthy from health
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
      abort with "The operator did not approve the note."
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
      abort with "The lead did not approve the shipment."
  exec check goods from checks as results
  verify #ready goods are ready from results
    otherwise:
      abort with "Goods are not ready to ship."
  write #ship shipment with shipments
  return shipment as shipment
```
