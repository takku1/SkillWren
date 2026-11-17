# Guarded config write

```contract
inputs:
  config
resources:
  production_config:
    path: the production config
    access: write
    immutable: false
order:
  verify #debug_off before write #prod_write
always:
  never write an unverified config
```

```logic
guarded-config-write:
  require config exists
    otherwise:
      abort with "A config is required."

  verify #debug_off config has debug off
    otherwise:
      abort with "Config verification failed: debug is not off."

  write #prod_write config with production_config

  return config as config
```
