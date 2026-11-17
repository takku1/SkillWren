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
  request, fast, draft, slot, report
order:
  verify#window_open before write#book_slot
  apply redaction before write#write_clean
  generate parts before generate assembly
  generate assembly before exec fresh check
  verify#assembly_match before write#write_assembly
```

```logic
f16:
  if fast flag is set:
    apply fast path with request as request
  return request as request

f17:
  exec window check from checks as window_status
  verify #window_open window is open from window_status
    otherwise:
      abort with "The window shut."
  write #book_slot slot with bookings
  return slot as booking

f18:
  apply redaction with draft as clean
  write #write_clean clean with output
  return clean as result

f19:
  generate parts from request as parts
  generate assembly from parts as assembly
  exec fresh check from checks as check
  verify #assembly_match assembly matches check from check
    otherwise:
      abort with "The assembly does not match the fresh check."
  write #write_assembly assembly with output
  return assembly as result

f20:
  show report
  return report as report
```

## Step meanings

- **fast path**: the shortened handling of the request, taken only when the fast flag is set.
- **redaction**: remove sensitive content from the draft in memory, producing the clean result.


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:20: error V1: unknown statement 'f17:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:21: error O1: 'exec window check from checks as window_status' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:22: error O1: 'verify #window_open window is open from window_status' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:25: error O1: 'write #book_slot slot with bookings' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:26: error O1: 'return slot as booking' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:28: error V1: unknown statement 'f18:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:29: error O1: 'apply redaction with draft as clean' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:30: error O1: 'write #write_clean clean with output' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:31: error O1: 'return clean as result' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:33: error V1: unknown statement 'f19:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:34: error O1: 'generate parts from request as parts' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:35: error O1: 'generate assembly from parts as assembly' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:36: error O1: 'exec fresh check from checks as check' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:37: error O1: 'verify #assembly_match assembly matches check from check' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:40: error O1: 'write #write_assembly assembly with output' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:41: error O1: 'return assembly as result' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:43: error V1: unknown statement 'f20:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:44: error O1: 'show report' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:45: error O1: 'return report as report' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:7: warning W13: order rule never applies: no statement starts with 'write#book_slot' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:8: warning W13: order rule never applies: no statement starts with 'write#write_clean' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:8: warning W15: order rule rests on self-report: every statement matching 'apply redaction' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:9: warning W13: order rule never applies: no statement starts with 'generate assembly' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:9: warning W15: order rule rests on self-report: every statement matching 'generate parts' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:10: warning W13: order rule never applies: no statement starts with 'exec fresh check' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:10: warning W15: order rule rests on self-report: every statement matching 'generate assembly' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:11: warning W13: order rule never applies: no statement starts with 'write#write_assembly' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:20: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:21: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:21: warning W5: binding 'window_status' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:22: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:23: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:24: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:25: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:26: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:28: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:29: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:29: warning W5: binding 'clean' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:30: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:31: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:33: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:34: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:34: warning W5: binding 'parts' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:35: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:35: warning W5: binding 'assembly' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:36: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:36: warning W5: binding 'check' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:37: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:38: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:39: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:40: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:41: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:43: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:44: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs16\draft.md:45: warning W10: unreachable statement -- Remove it or fix the control flow.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
