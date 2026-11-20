# --version flag design note

- `main()` checks `argv[0] == "--version"` first, prints `VERSION` ("1.0"), returns 0.
- Version lives in a module constant `VERSION` in `src/app.py`; no argparse, matching the existing hand-rolled parsing.
- The flag short-circuits before any item handling, so it never prints the todo list.
