# Read-only summary

The request must exist; the flow summarizes it for the log and touches
nothing.

```logic
summarize:
  require request exists
    otherwise:
      abort with "Nothing to summarize."
  generate summary from request as summary
  return summary as summary
```
