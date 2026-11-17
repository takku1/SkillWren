# Batch 4 intents

f16: Take the fast path only when the fast flag is set; otherwise skip
it and return the request.

f17: Act only while the window is open: verify it, abort if it shut,
and book the slot inside the window.

f18: Redact the draft and write the clean result. Redaction happens
in memory first.

f19: Build in stages: generate parts, generate the assembly from them,
verify the assembly against a fresh check, then write it. Mismatch
aborts.

f20: Show the audit report to the requester. Showing is advisory:
nothing here can be enforced.


Your previous draft was:

# Batch 4 flows

```contract
inputs:
  request, fast, window, slot, draft, request, audit_report
order:
  verify#window before write#book
  apply redaction before write clean
  generate parts before generate assembly
  verify#match before write#out
```

```logic
f16:
  if fast flag is set:
    apply fast path with request as fast_result
  return request as request
```

```logic
f17:
  verify #window window is open
    otherwise:
      abort with "The window shut."
  write #book slot with bookings
```

```logic
f18:
  apply redaction with draft as clean
  write clean with output
```

```logic
f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec fresh check from checks as check
  verify #match assembly matches check from check
    otherwise:
      discard assembly
      abort with "Assembly does not match the fresh check."
  write #out assembly with output
```

```logic
f20:
  show audit_report
```

## Step meanings

- **fast path**: the fast-path handling of the request, performed only when the fast flag is set.
- **redaction**: redact the draft in memory, producing the clean result before anything is written.


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:25: error R2: flow falls off the end without return or abort -- End every path with a return or abort.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:29: error R2: flow has no reachable return or abort -- End the flow with a return or abort.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:31: error R2: flow falls off the end without return or abort -- End every path with a return or abort.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:43: error R2: flow falls off the end without return or abort -- End every path with a return or abort.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:47: error R2: flow has no reachable return or abort -- End the flow with a return or abort.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:48: error R2: flow falls off the end without return or abort -- End every path with a return or abort.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:7: warning W15: order rule rests on self-report: every statement matching 'verify#window' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:8: warning W15: order rule rests on self-report: every statement matching 'apply redaction' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:9: warning W15: order rule rests on self-report: every statement matching 'generate parts' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\pairs16\draft.md:16: warning W5: binding 'fast_result' never referenced -- Use it or drop the `as`.

Return a corrected full fragment that fixes these errors without changing what the intent requires.
