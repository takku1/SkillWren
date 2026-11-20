# --version flag

- `src/app.py` checks `argv[0] == "--version"` before the `add` handling, prints `1.0`, and returns 0.
- Version lives in a module constant `VERSION = "1.0"`.
- Hand-rolled argv check (no argparse) to match the existing style of the CLI.
