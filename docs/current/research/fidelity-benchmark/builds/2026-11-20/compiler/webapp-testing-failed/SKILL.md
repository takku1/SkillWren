---
name: webapp-testing
description: Test and debug local web applications with native Python Playwright scripts: verify frontend functionality, debug UI behavior, capture screenshots, view browser logs, and start servers with the bundled with_server.py helper. Use when asked to test, inspect, or screenshot a local web app or static HTML page. Not for remote sites, non-browser testing, or editing the app's source.
---

# Web application testing (SkillWren logic)

The procedure is the `logic` block below, with its `contract` rules. Execute it exactly; it is the only procedure.

```contract
always:
  write native Python Playwright scripts for testing local web applications
  run bundled scripts directly as black boxes, starting with --help
  keep the automation script to Playwright logic only when with_server.py manages the servers
  launch chromium headless with sync_playwright and p.chromium.launch(headless=True)
  close the browser when automation is done
never:
  read a bundled script's source unless running it with --help was tried and a customized solution is absolutely necessary
  inspect the DOM before waiting for networkidle on dynamic apps
inputs:
  target, automation_script, inspect_png, with_server
order:
  verify#help before exec#servers
  apply navigate and wait for networkidle before write#inspect
  write#inspect before apply identify selectors
  apply identify selectors before exec#actions
```

```logic
test-webapp:
  if target is static HTML:
    read #html the target HTML file directly as html
      otherwise:
        return to dynamic
    verify #html-complete html is complete enough to identify selectors from html
      otherwise:
        return to dynamic
    apply find static selectors with html as selectors
    generate native Python Playwright script from selectors as script
    write #script-static script with automation_script
    return script as script
  label dynamic:
  if server is already running:
    apply navigate and wait for networkidle with target as page
    write #inspect full-page screenshot of page with inspect_png
    apply inspect rendered DOM with page as dom
    apply identify selectors with dom as selectors
    generate Playwright script from selectors as script
    write #script-recon script with automation_script
    exec #actions run automation script from automation_script as result
    return result as result
  else:
    exec #help-run python scripts/with_server.py --help from with_server as help
    verify #help usage was read from the help output from help
    if a customized solution is absolutely necessary after the --help run:
      read #source the with_server.py source as source
        otherwise:
          apply record missing source as a gap with help as help
      apply customize helper use with source as help
    generate simplified Playwright script from target as script
    write #script-dynamic script with automation_script
    exec #servers with_server.py with one --server and --port pair per server, then the automation script from with_server as result
    return result as result
```

## Context

Toolkit for interacting with and testing local web applications using Playwright: verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.

Bundled scripts can be very large. Call them with `--help` and use them as black boxes so they do not fill the context window.

## Step meanings

- **find static selectors**: read the static HTML and identify the selectors the script will use. If the HTML cannot be read or is incomplete, treat the target as a dynamic webapp.
- **navigate and wait for networkidle**: `page.goto(url)`, then `page.wait_for_load_state('networkidle')` so JS has executed. This is critical on dynamic apps.
- **inspect rendered DOM**: read `page.content()` and list `page.locator('button').all()`, alongside the screenshot.
- **identify selectors**: take selectors from the rendered state, using the screenshot, `page.content()`, and `page.locator('button').all()`. Selectors are `text=`, `role=`, CSS, or IDs.
- **full-page screenshot** (the `write#inspect` step): `page.screenshot(path='/tmp/inspect.png', full_page=True)`.
- **record missing source as a gap**: note that the source was unavailable and continue with what `--help` showed.
- **customize helper use**: adapt how the helper is invoked using what the source shows.

## Commands

`--server` takes a server's start command and `--port` its port; repeat the pair for each server. The automation command follows `--`.

| Flow step | Command |
|---|---|
| `exec #help-run` | `python scripts/with_server.py --help` |
| `exec #servers` (single) | `python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_automation.py` |
| `exec #servers` (multiple) | `python scripts/with_server.py --server "cd backend && python server.py" --port 3000 --server "cd frontend && npm run dev" --port 5173 -- python your_automation.py` |
| `exec #actions` | `python your_automation.py` (server already running) |

The automation script has this shape:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    # ... automation logic
    browser.close()
```

## Taste

Use descriptive selectors (`text=`, `role=`, CSS selectors, or IDs). Add appropriate waits with `page.wait_for_selector()` or `page.wait_for_timeout()`. Use judgment on both.

## Reference examples

Consult `examples/` when a matching pattern helps. Each file is optional, and a missing one is only a gap.

- `element_discovery.py`: discover buttons, links, and inputs on a page.
- `static_html_automation.py`: use `file://` URLs for local HTML.
- `console_logging.py`: capture console logs during automation.
