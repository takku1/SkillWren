# Intent 01: guarded config write

Before writing the production config, verify it has debug off. If
verification fails, abort and report the reason. Never write an
unverified config.


Your previous draft was:

```contract
inputs:
  config
order:
  verify#debug_off before write#config_write
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
      abort with "Verification failed: the production config does not have debug off."

  write #config_write config with production_config

  return config as config
```


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\01\draft.md:1: error F2: contract sections out of order -- Use always:, never:, inputs:, order: in that order.
Z:\SkillWren\docs\current\research\nl-fidelity\model-draft\sonnet\01\draft.md:5: warning W13: order rule never applies: no statement starts with 'write#config_write' -- Fix the pattern so it matches the later statement, or drop the rule.

Return a corrected full fragment that fixes these errors without changing what the intent requires.
