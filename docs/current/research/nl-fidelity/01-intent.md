# Intent 01: guarded config write

Before writing the production config, verify it has debug off. If
verification fails, abort and report the reason. Never write an
unverified config.
