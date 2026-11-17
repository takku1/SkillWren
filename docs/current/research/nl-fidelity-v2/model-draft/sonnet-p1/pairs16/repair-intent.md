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
order:
  verify#window before write#slot
  apply redaction before write#clean
  generate assembly before exec fresh check
  verify#match before write#assembled
```

```logic
f16:
  if fast flag is set:
    apply fast path with request as request
  return request as request
```

```logic
f17:
  verify #window window is open
    otherwise:
      abort with "The window has shut."
  write #slot slot with booking
  return
```

```logic
f18:
  apply redaction with draft as clean
  write #clean clean with destination
  return
```

```logic
f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec fresh check from checks as check
  verify #match assembly matches fresh check from check
    otherwise:
      discard assembly
      abort with "Assembly does not match the fresh check."
  write #assembled assembly with target
  return
```

```logic
f20:
  show audit report
  return
```

## Step meanings

- **fast path**: the shortened route for the request, taken only when the fast flag is set.
- **redaction**: remove sensitive content from the draft, in memory, producing the clean result.


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:14: error U1: apply target 'request' may be unbound on some path -- Bind it on every path to this use.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:15: error U1: return value 'request' may be unbound on some path -- Bind it on every path to this use.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:24: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:31: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:44: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:50: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:5: warning W15: order rule rests on self-report: every statement matching 'verify#window' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:6: warning W15: order rule rests on self-report: every statement matching 'apply redaction' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:7: warning W15: order rule rests on self-report: every statement matching 'generate assembly' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs16\draft.md:29: warning W5: binding 'clean' never referenced -- Use it or drop the `as`.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
