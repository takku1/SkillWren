# Summarize request

```contract
inputs:
  request
```

```logic
summarize-request:
  require request exists
    otherwise:
      abort with "A request is required."

  generate summary from request as summary

  return summary as summary
```
