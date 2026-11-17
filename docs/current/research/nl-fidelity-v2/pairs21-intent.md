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
