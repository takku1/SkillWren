# Read-only summary

The request must exist; the flow returns it unchanged and touches
nothing.

```logic
summarize:
  require request exists
    otherwise:
      abort with "Nothing to summarize."
  return request as request
```
