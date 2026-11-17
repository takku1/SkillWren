# Batch 3 intents

f11: Rotate an access key only after its holder approves. Refusal aborts
and nothing is written.

f12: Observe the audit check and return its report. Nothing is written
and no decision is needed.

f13: Copying needs both ends to exist: require the source and the
destination before writing the copy.

f14: Process every item in turn and write each processed item, then
return the items.

f15: Return the request unchanged in a return block. A missing request
aborts.


Your previous draft was:

# Batch 3 flows

```contract
inputs:
  key, source, destination, items, item_store, request
order:
  require source exists before write copy
  require destination exists before write copy
```

```logic
f11:
  ask #approval key holder to approve access key rotation
  require confirmation
    otherwise:
      abort with "Rotation refused by the key holder."
  write #rotation rotation with key
  return
```

```logic
f12:
  exec readonly audit check from checks as report
  return report as report
```

```logic
f13:
  require source exists
    otherwise:
      abort with "The source is required."
  require destination exists
    otherwise:
      abort with "The destination is required."
  write #copy source with destination
  return
```

```logic
f14:
  for each items as item:
    apply processing with item as processed
    write processed with item_store
  return items as items
```

```logic
f15:
  require request exists
    otherwise:
      abort with "A request is required."
  return:
    request
```

## Step meanings

- **processing**: process one item and bind the processed result; the item itself is not modified.


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs11\draft.md:18: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs11\draft.md:36: error V1: malformed return 'return' -- Use `return <binding> as <name>` or a `return:` block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs11\draft.md:7: warning W13: order rule never applies: no statement starts with 'write copy' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs11\draft.md:7: warning W15: order rule rests on self-report: every statement matching 'require source exists' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs11\draft.md:8: warning W13: order rule never applies: no statement starts with 'write copy' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\pairs11\draft.md:8: warning W15: order rule rests on self-report: every statement matching 'require destination exists' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
