---
name: webapp-testing
description: Test and debug local web applications with native Python Playwright scripts, using the bundled with_server.py helper to start servers. Use to verify frontend behavior, debug UI, capture browser screenshots, or view browser logs. Not for testing remote or production sites.
---

# Web application testing (SkillWren logic)

The procedure is the `logic` block below, with its `contract`. Execute it exactly; it is the only procedure.

```contract
always:
  treat bundled scripts as black boxes and invoke them directly
  launch chromium in headless mode
  use sync_playwright for synchronous scripts
  close the browser when done
  use descriptive selectors: text=, role=, CSS selectors, or IDs
  add appropriate waits with wait_for_selector or wait_for_timeout
  keep automation scripts to Playwright logic only, since with_server manages servers
never:
  read helper script source before running it with --help
inputs:
  target, automation_file, inspect_png
order:
  exec#help before write#script
  exec#help before exec#single
  exec#help before exec#multi
  write#script before exec#single
  write#script before exec#multi
  apply navigate and wait for networkidle before apply inspect rendered state
  apply navigate and wait for networkidle before write#shot
  apply inspect rendered state before apply identify selectors
  apply identify selectors before apply execute actions
  apply execute actions before apply close browser
```

```logic
webtest:
  if target is static HTML:
    read html file from target as html
      otherwise:
        return to dynamic
    generate Playwright script from html as script
    return script as result
  label dynamic:
  if server is already running:
    apply navigate and wait for networkidle with target as ready_page
    apply inspect rendered state with ready_page as inspection
    write #shot inspection with inspect_png
    apply identify selectors with inspection as selectors
    apply execute actions with selectors as result
    apply close browser with result as closed
    return closed as result
  else:
    exec #help with_server help from checks as help
    verify #usage help output shows enough usage to run the helper from help
      otherwise:
        read helper source from scripts as source
          otherwise:
            apply record source gap with help as gap
            return to launch
        apply customized solution with source as helper_plan
        return to launch
    label launch:
    generate simplified Playwright script from target as automation_script
    write #script automation_script with automation_file
    if multiple servers are needed:
      exec #multi with_server multiple servers from checks as run_result
    else:
      exec #single with_server single server from checks as run_result
    return run_result as result
```

## Context

To test local web applications, write native Python Playwright scripts. `scripts/with_server.py` manages server lifecycle and supports multiple servers. Scripts can be very large: call them as black boxes and keep their source out of the context window.

An automation script passed to `with_server.py` holds only Playwright logic; the helper starts the servers. Launch chromium headless, and open the page with `page.goto(url)`. Then call `page.wait_for_load_state('networkidle')` before any inspection of a dynamic app. This is critical because it waits for JS to run. Close the browser at the end. `inspect_png` is `/tmp/inspect.png`.

## Step meanings

- **navigate and wait for networkidle**: `goto` the app URL, then `page.wait_for_load_state('networkidle')`. Never inspect the DOM of a dynamic app before this wait.
- **inspect rendered state**: take `page.screenshot(path='/tmp/inspect.png', full_page=True)`, read `page.content()`, and list `page.locator('button').all()`.
- **identify selectors**: choose selectors from the rendered state, not from guesses.
- **execute actions**: run the test actions with the discovered selectors.
- **close browser**: `browser.close()`.
- **customized solution**: adapt the helper using what its source shows. Do this only when `--help` was run and a customized solution is absolutely necessary.
- **record source gap**: state that the helper source could not be read, so no customized solution was made, and continue.

## Commands

| Flow step | Command |
|---|---|
| `exec #help` | `python scripts/with_server.py --help` |
| `exec #single` | `python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_automation.py` |
| `exec #multi` | `python scripts/with_server.py --server "cd backend && python server.py" --port 3000 --server "cd frontend && npm run dev" --port 5173 -- python your_automation.py` |

On Windows use `py -3` when `python` is a Microsoft Store stub.

## Reference examples

The `examples/` folder is optional. Consult it when a pattern is needed:

- `element_discovery.py` finds buttons, links, and inputs on a page.
- `static_html_automation.py` uses `file://` URLs for local HTML.
- `console_logging.py` captures console logs during automation.

If `examples/` is missing, carry on without it.
