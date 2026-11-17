# Production deploy approval gate

```contract
order:
  ask#approve before exec deploy
```

```logic
approve-production-deploy:
  ask #approve user to approve the deploy

  require confirmation
    otherwise:
      abort with "Deploy not approved. Nothing was deployed."

  exec deploy from deploy as result
  return result as deployment
```
