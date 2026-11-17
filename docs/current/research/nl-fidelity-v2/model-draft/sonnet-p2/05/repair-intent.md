# Intent 05: read-only summary

Summarize the request for the log. Nothing is written and no human
decision is needed; a missing request aborts the run.


Your previous draft was:

# Summarize request

```contract
inputs:
  request
never:
  write any file or resource
```

```logic
summarize-request:
  require request exists
    otherwise:
      abort with "A request is required."

  generate summary from request as summary

  return summary as summary
```


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p2\05\draft.md:3: error F2: contract sections out of order -- Use always:, never:, inputs:, order: in that order.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
