```contract
order:
  ask#approval before exec deploy
```

```logic
deploy-to-production:
  ask #approval user to approve deploy
  require confirmation
    otherwise:
      abort with "Deploy not confirmed; nothing was deployed."

  exec deploy from deploy_tool as result
  return result as deploy_result
```
