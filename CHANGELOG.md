# Changelog

## 0.3.0 (2026-10-01)

- Rebrand: the project is now **SkillWren** (`skillwren` package, `skillwren`
  CLI). Validator behavior is unchanged.
- Packaging: new `pyproject.toml` (setuptools, stdlib-only, `skillwren`
  console script), `LICENSE` (MIT), `.gitignore`.
- Layout: single doc set in `docs/` (drops the `docs/superpowers/specs` vs
  `src/` mirror); examples in `examples/`; benchmark evidence in
  `benchmarks/`; unit suite stays in `tests/`. Pruned exact-duplicate files
  (`test/pkg/SKILL.md`, mirrored spec set).
- CLI: `skillwren check <file>...` (exit 0 clean, 1 on errors), also
  available as `python -m skillwren check <file>...`.
- Spec: Section 15 now describes the shipped CLI surface; `--all` and
  `--explain` are deferred to a later release.
