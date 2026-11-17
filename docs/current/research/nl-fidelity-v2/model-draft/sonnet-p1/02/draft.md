# Deploy to production with human approval

```contract
order:
  ask#approve before exec#deploy
```

```logic
deploy-to-production:
  ask #approve user to approve the deploy to production
  require confirmation
    otherwise:
      abort with "Deploy not approved; nothing was deployed."

  exec #deploy deploy to production from production as result
  return result as result
```
