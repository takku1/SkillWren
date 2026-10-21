Example input:

```text
Delete temporary files after success, except diagnostic logs. On failure,
preserve every file until the user has reviewed the error.
```

Faithful summary: after success, delete temporary files except diagnostic logs;
on failure, preserve everything pending user review.

Unfaithful summary: delete temporary files when finished. This loses both the
log exception and the failure condition.
