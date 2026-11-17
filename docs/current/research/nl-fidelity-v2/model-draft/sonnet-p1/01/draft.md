# Guarded config write

```contract
never:
  write an unverified config
inputs:
  config
order:
  verify#debug_off before write#prod_write
```

```logic
guarded-config-write:
  require config exists
    otherwise:
      abort with "A config is required."

  exec debug off check from checks as screen
  verify #debug_off config has debug off from screen
    otherwise:
      abort with "Config verification failed: debug is not off."

  write #prod_write config with production_config

  return config as config
```
