# --version flag

`src/app.py` checks `argv[0]` for `--version`, prints `1.0` and returns 0
before any todo handling. Kept as a manual check (not argparse) to match the
existing hand-rolled argv parsing. Version lives in a `VERSION` constant.
