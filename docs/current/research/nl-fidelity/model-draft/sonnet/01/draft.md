# Guarded config write

```contract
never:
  write an unverified config
inputs:
  config
order:
  verify#debug_off before write config
```

```logic
guarded-config-write:
  require config exists
    otherwise:
      abort with "A config is required."

  verify #debug_off config has debug off
    otherwise:
      abort with "Verification failed: the production config does not have debug off."

  write config with production_config

  return config as config
```
