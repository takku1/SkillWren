# Guarded config write

```contract
inputs:
  config
order:
  verify#debug-off before write#prod-config
```

```logic
guarded-config-write:
  exec debug off check from checks as debug_check
  verify #debug-off config has debug off from debug_check
    otherwise:
      abort with "Config verification failed: debug is not off."

  write #prod-config config with production_config

  return config as config
```
