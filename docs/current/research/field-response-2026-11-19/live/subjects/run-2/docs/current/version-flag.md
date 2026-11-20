# --version flag

- `main` checks `argv[0] == "--version"`, prints `1.0`, returns 0 before any other handling.
- Version lives in a module constant `__version__ = "1.0"` so it has one source of truth.
- No argparse: the CLI is hand-parsed, so a single early check matches existing style.
