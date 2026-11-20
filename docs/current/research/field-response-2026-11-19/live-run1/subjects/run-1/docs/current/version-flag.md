# --version flag

- `main` checks `argv` for `--version` first, prints `1.0`, returns 0.
- Version lives in a module constant `VERSION` so it has one place to change.
- Handled by hand (no argparse) to match the existing minimal CLI.
