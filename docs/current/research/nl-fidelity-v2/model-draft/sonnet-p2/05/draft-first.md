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
