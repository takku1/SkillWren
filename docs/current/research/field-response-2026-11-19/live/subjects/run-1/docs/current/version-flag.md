# --version flag

- `main()` checks `argv[0] == "--version"`, prints `1.0`, returns 0 before any other handling.
- Version lives in a module constant `VERSION` so it has one source of truth.
- Kept hand-rolled (no argparse) to match the existing minimal CLI.
