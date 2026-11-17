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
  return
```

```logic
f22:
  exec check service health from service as health
  verify service is healthy from health
    otherwise:
      exec restart service from service as restarted
      exec check service health from service as health
      verify service is healthy from health
        otherwise:
          exec reload service from service as reloaded
          exec check service health from service as health
          verify service is healthy from health
            otherwise:
              abort with "Service is still unhealthy after restart and reload."
  return health as state
```

```logic
f23:
  ask operator to approve note
  require confirmation
    otherwise:
      abort with "The operator did not approve the note."
  write note with notes
  return
```

```logic
f24:
  write note with notes
  return
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
  return
```


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:21: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:48: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:54: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:68: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:28: warning W9: otherwise: block falls through -- End it with retry, return to, abort, or return.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:29: warning W5: binding 'restarted' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:32: warning W9: otherwise: block falls through -- End it with retry, return to, abort, or return.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs21\draft.md:33: warning W5: binding 'reloaded' never referenced -- Use it or drop the `as`.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
