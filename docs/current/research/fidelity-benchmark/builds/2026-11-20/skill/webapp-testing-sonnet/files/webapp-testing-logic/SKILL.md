---
name: webapp-testing
description: Test and interact with local web applications using native Python Playwright scripts. Verifies frontend functionality, debugs UI behavior, captures screenshots and browser logs. Use when asked to test, drive or inspect a local web app.
---

# Web Application Testing

```contract
inputs:
  request, target
order:
  exec with_server help before exec with_server run
  verify #idle before generate action selectors
```

```logic
webapp-testing:
  require request exists
    otherwise:
      abort with "Say which local web app to test and what to check."

  label start:
  if the target is static HTML and not marked dynamic:
    read target html from target as html
      otherwise:
        apply dynamic marking with request as request
        return to start
    generate selectors from html as selectors
    verify #static the selectors are complete enough to script from selectors
      otherwise:
        apply dynamic marking with request as request
        return to start
    generate script from selectors as script
    apply script rules with script as script
    verify #rules the script follows every script rule from script
      otherwise:
        apply script rules with script as script
        retry
    write script with script_file
    exec automation run from launcher as result
  else:
    if the server is not already running:
      exec with_server help from launcher as usage
      verify #usage the help output was read from usage
        otherwise:
          abort with "with_server.py --help could not be run; its source stays unread until the script has been tried."
      generate simplified script from request and usage as script
      apply script rules with script as script
      verify #rules_helper the script follows every script rule from script
        otherwise:
          apply script rules with script as script
          retry
      write script with script_file
      exec with_server run from launcher as result
    else:
      generate recon script from request as recon_script
      apply script rules with recon_script as recon_script
      verify #rules_recon the recon script follows every script rule from recon_script
        otherwise:
          apply script rules with recon_script as recon_script
          retry
      write recon_script with script_file
      exec recon run from launcher as recon
      verify #idle the recon waited for networkidle before inspecting the DOM from recon
        otherwise:
          apply recon repair with recon_script as recon_script
          write recon_script with script_file
          exec recon run from launcher as recon
          retry
      generate action selectors from recon as selectors
      generate script from selectors as script
      apply script rules with script as script
      verify #rules_action the script follows every script rule from script
        otherwise:
          apply script rules with script as script
          retry
      write script with script_file
      exec automation run from launcher as result

  show result
  return #tested:
    result
```

| Step | Command |
|---|---|
| `exec with_server help` | `python scripts/with_server.py --help` |
| `exec with_server run` | `python scripts/with_server.py --server "<cmd>" --port <port> [--server "<cmd>" --port <port> ...] -- python <script_file>` (one `--server`/`--port` pair per server, e.g. backend + frontend) |
| `exec recon run` | `python <script_file>` against the running server |
| `exec automation run` | `python <script_file>` (for static HTML, a `file://` URL) |

## Step meanings

- **launcher**: the project's shell; `scripts/with_server.py` is a black box: call it, never read its source unless running it showed a customized solution is absolutely necessary. **script_file**: the Playwright script the run writes.
- **target**: the web app, as a `file://` HTML path or a local URL. **dynamic marking**: record that the target is dynamic, not static, so the dynamic branch is taken.
- **recon script**: a Playwright script that navigates, waits for `networkidle`, then takes a full-page screenshot (`page.screenshot(path='/tmp/inspect.png', full_page=True)`), reads `page.content()` and lists `page.locator('button').all()`. It performs no other actions.
- **recon repair**: add the missing `page.wait_for_load_state('networkidle')` before any inspection.
- **script rules**: the script contains only Playwright logic (servers are managed by the helper); uses `sync_playwright()`; launches chromium with `headless=True`; calls `page.wait_for_load_state('networkidle')` after `goto` and before any DOM inspection on dynamic apps; uses descriptive selectors (`text=`, `role=`, CSS, IDs); adds appropriate waits (`page.wait_for_selector()` or `page.wait_for_timeout()`); always closes the browser when done.
- **simplified script**: the automation script for the helper: Playwright logic only, targeting the server the helper starts.
- Optional examples (not shipped here): `element_discovery.py` (discover buttons, links, inputs), `static_html_automation.py` (`file://` URLs), `console_logging.py` (capture console logs).
