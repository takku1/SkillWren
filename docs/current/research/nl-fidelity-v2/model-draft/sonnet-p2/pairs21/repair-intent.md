# Batch 5 intents

f21ingest: Read the request and return it unchanged.
f21store: Require a record, then write it. Two small flows, one file.

f22: A healthy service returns its state. On failure restart, then
reload, then give up with an error if still unhealthy.

f23: The operator must approve the note before it is written. No
ordering rule governs this flow beyond the written sequence.

f24: Record a note that was already verified elsewhere. This flow
verifies nothing itself.

f25: Ship only approved, ready goods: ask the lead, confirm, check,
verify readiness, then write the shipment.


Your previous draft was:

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
      exec restart service from checks as restart
      exec health check from checks as health
      verify #restarted service is healthy from health
        otherwise:
          exec reload service from checks as reload
          exec health check from checks as health
          verify #reloaded service is healthy from health
            otherwise:
              abort with "Service is still unhealthy after restart and reload."

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

  write #shipwrite shipment with shipments
  return shipment as shipment
```


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs21\draft.md:74: error U1: return value 'shipment' is not bound -- Bind it with `as` or list it under the contract's inputs:.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs21\draft.md:30: warning W9: otherwise: block falls through -- End it with retry, return to, abort, or return.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs21\draft.md:31: warning W5: binding 'restart' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs21\draft.md:34: warning W9: otherwise: block falls through -- End it with retry, return to, abort, or return.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs21\draft.md:35: warning W5: binding 'reload' never referenced -- Use it or drop the `as`.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
