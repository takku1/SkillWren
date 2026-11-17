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
  access_key, holder, source, destination, items, request
order:
  ask#approve_rotation before write#rotate_key
```

```logic
f11:
  ask #approve_rotation holder to approve access key rotation
  require confirmation
    otherwise:
      abort with "The holder refused the rotation."
  write #rotate_key access_key with access_key
  return access_key as access_key

f12:
  exec audit check from checks as report
  return report as report

f13:
  require source exists
    otherwise:
      abort with "The source is required."
  require destination exists
    otherwise:
      abort with "The destination is required."
  write #write_copy source with destination
  return destination as destination

f14:
  for each items as item:
    apply processing with item as processed
    write #write_item processed with processed_items
  return items as items

f15:
  require request exists
    otherwise:
      abort with "A request is required."
  return:
    request
```

## Step meanings

- **processing**: process one item as the task defines; the item itself is not modified in place.


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:19: error V1: unknown statement 'f12:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:20: error O1: 'exec audit check from checks as report' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:21: error O1: 'return report as report' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:23: error V1: unknown statement 'f13:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:24: error O1: 'require source exists' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:27: error O1: 'require destination exists' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:30: error O1: 'write #write_copy source with destination' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:31: error O1: 'return destination as destination' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:33: error V1: unknown statement 'f14:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:34: error O1: 'for each items as item:' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:37: error O1: 'return items as items' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:39: error V1: unknown statement 'f15:' -- Use only the v0.6 verb set.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:40: error O1: 'require request exists' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:43: error O1: 'return:' cannot nest here -- Dedent it or move it into a branch or repair block.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:7: warning W13: order rule never applies: no statement starts with 'write#rotate_key' -- Fix the pattern so it matches the later statement, or drop the rule.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:19: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:20: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:20: warning W5: binding 'report' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:21: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:23: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:24: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:25: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:26: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:27: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:28: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:29: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:30: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:31: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:33: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:34: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:34: warning W5: binding 'item' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:35: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:35: warning W5: binding 'processed' never referenced -- Use it or drop the `as`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:36: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:37: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:39: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:40: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:41: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:42: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:43: warning W10: unreachable statement -- Remove it or fix the control flow.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\pairs11\draft.md:44: warning W10: unreachable statement -- Remove it or fix the control flow.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
