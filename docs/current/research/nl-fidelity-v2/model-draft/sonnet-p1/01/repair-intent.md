# Intent 01: guarded config write

Before writing the production config, verify it has debug off. If
verification fails, abort and report the reason. Never write an
unverified config.


Your previous draft was:

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


`skillwren check --fragment` reported:

Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:3: error F2: contract sections out of order -- Use always:, never:, inputs:, order: in that order.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:6: error F2: unexpected 'resources:' in contract block -- Only always:/never:/inputs:/order: live here.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:7: error F2: input 'production_config:' is not a binding name -- List bare binding names, for example `request, design`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:8: error F2: input 'path:' is not a binding name -- List bare binding names, for example `request, design`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:9: error F2: input 'access:' is not a binding name -- List bare binding names, for example `request, design`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:10: error F2: input 'immutable:' is not a binding name -- List bare binding names, for example `request, design`.
Z:\SkillWren\docs\current\research\nl-fidelity-v2\model-draft\sonnet-p1\01\draft.md:12: warning W15: order rule rests on self-report: every statement matching 'verify #debug_off' is the model's own judgment -- Anchor it to something observable: `verify ... from <exec result>`, an exec, a written artifact, or a user decision.

Return a corrected full fragment that fixes these problems without changing what the intent requires.
