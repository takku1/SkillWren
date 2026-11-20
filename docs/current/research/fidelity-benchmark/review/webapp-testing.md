# Requirement review: webapp-testing

Source: sources/webapp-testing/SKILL.md
Reviewed by: <your name>
Date: <YYYY-MM-DD>

**How to review.** These are model-drafted candidates. For each line: keep it
(`[x]`), drop it (change to `[ ]`), or edit the requirement text so it says
what the source really requires. Add anything missing as a new line with the
next free ID (`WT-15`, ...); quote the source span, or write `inferred` if you
accept it without one. Kinds: obligation, prohibition, exception, ordering,
authority, output. Then fill in the two lines above.

Ask of each line: if a converted skill lost or weakened this, would the skill
be wrong? If not, drop it.

- [x] WT-1 | obligation | Test local web applications by writing native Python Playwright scripts. | "write native Python Playwright scripts"
- [x] WT-2 | ordering | Run a helper script with `--help` before using it. | "Always run scripts with `--help` first"
- [x] WT-3 | prohibition | Do not read a helper script's source unless running it showed that a customized solution is absolutely necessary. | "DO NOT read the source until you try running the script first"
- [x] WT-4 | obligation | Before writing custom code, consider whether a bundled script in `scripts/` can do the job, and use it as a black box. | "consider whether one of the scripts available in `scripts/` can help"
- [x] WT-5 | exception | For static HTML, read the HTML file directly to identify selectors; if that fails or is incomplete, treat the app as dynamic. | "Read HTML file directly to identify selectors"
- [x] WT-6 | exception | For a dynamic app whose server is not running, use `scripts/with_server.py` (after `--help`) to manage the server. | "Run: python scripts/with_server.py --help"
- [x] WT-7 | ordering | On dynamic apps, wait for `networkidle` before inspecting the DOM. | "inspect the DOM before waiting for `networkidle` on dynamic apps"
- [x] WT-8 | ordering | Reconnaissance before action: inspect the rendered page (screenshot or DOM), identify selectors from it, then act with those selectors. | "Identify selectors from rendered state"
- [x] WT-9 | obligation | Automation scripts contain only Playwright logic; the helper manages servers. | "include only Playwright logic (servers are managed automatically)"
- [x] WT-10 | obligation | Launch Chromium in headless mode. | "Always launch chromium in headless mode"
- [x] WT-11 | obligation | Always close the browser when done. | "Always close the browser when done"
- [x] WT-12 | obligation | Use `sync_playwright()` for synchronous scripts. | "Use `sync_playwright()` for synchronous scripts"
- [x] WT-13 | obligation | Use descriptive selectors (`text=`, `role=`, CSS selectors or IDs). | "Use descriptive selectors"
- [x] WT-14 | obligation | Add appropriate waits (`wait_for_selector` or `wait_for_timeout`). | "Add appropriate waits"
