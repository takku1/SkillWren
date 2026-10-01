(A) REVIEW REPORT (review-file → target.py)

Verdict: Do not merge — critical findings must be fixed. No approval.

Findings ranked critical → major → minor. All findings grounded in quoted code.

CRITICAL

1. SQL injection in `get_user`
Evidence: `cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")` [target.py:14]
Impact: attacker-controlled `user_id` executes arbitrary SQL.
Fix: `cursor.execute("SELECT * FROM users WHERE id = ?", [user_id])`

2. Insecure deserialization via pickle
Evidence: `prefs = pickle.loads(user[3])` [target.py:27] with `import pickle` [target.py:2]
Impact: attacker-controlled DB value gives arbitrary code execution.
Fix: store JSON and use `json.loads(user[3])`; do not unpickle untrusted data.

3. Hardcoded secret
Evidence: `API_KEY = "[REDACTED]"` [target.py:7]
Impact: credential leaks in source/history.
Fix: read from environment, e.g. `API_KEY = os.environ["API_KEY"]`, rotate the key.

MAJOR

4. Unescaped HTML / XSS
Evidence: `html = "<h1>Hi " + user[1] + "</h1>"` [target.py:26]
Impact: user-controlled name injects HTML/JS.
Fix: `import html` then `html.escape(user[1])`.

5. Swallowed notification failure
Evidence:
```
    try:
        requests.get(f"https://api.example.com/notify/{order_id}")
    except Exception:
        pass
```
[target.py:20-23]
Impact: failed notifications silently lost; bugs hidden.
Fix: log and propagate/handle: `except requests.RequestException: logger.exception(...); raise` or retry.

6. Crash on missing user
Evidence: `user = get_user("shop.db", user_id)` [target.py:19] then `if user[2] == 3:` [target.py:25]; `get_user` returns `cursor.fetchone()` [target.py:15] which may be `None`.
Impact: `TypeError` on unknown user.
Fix: `if user is None: return None, None` (or raise).

7. N+1 queries in `outstanding_totals`
Evidence:
```
    for uid in user_ids:
        row = conn.execute("SELECT total FROM orders WHERE user_id = ?", [uid]).fetchone()
```
[target.py:35-36]
Impact: one round-trip per user; slow at scale.
Fix: single batched query with `WHERE user_id IN (...)` and map results.

8. Unclosed DB connections
Evidence: `conn = sqlite3.connect(db_path)` [target.py:12] and [target.py:33] with no `close()`.
Impact: connection/cursor leaks.
Fix: `with sqlite3.connect(db_path) as conn:`.

MINOR

9. Magic number + brittle tuple indexing; unused constant
Evidence: `SHIPPED = 3` [target.py:8] but `if user[2] == 3:` [target.py:25]
Impact: readability/maintenance; breaks if column order changes.
Fix: `if user[2] == SHIPPED:`; prefer named columns/`Row`.

10. Unbounded HTTP call, no timeout
Evidence: `requests.get(f"https://api.example.com/notify/{order_id}")` [target.py:21]
Impact: can hang caller indefinitely.
Fix: `requests.get(..., timeout=5)`.

No code was modified. No approval given due to critical findings.

---

(B) META

Flow executed (review-file, in order):
1. require target exists → PASS (target.py present and readable)
2. read target from tree as content → done
3. generate findings from content as findings → done (10 findings)
4. generate suggested fixes from findings as fixes → done (10 minimal fixes)
5. verify every finding has quoted evidence → PASS (all findings quote exact lines)
6. show findings → done (in report above)
7. show fixes → done (in report above)
8. ask user which findings to dispute as disputed → WOULD-ASK, continued with best judgment (kept=all)
9. require confirmation → assumed PASS headless (best judgment: proceed, no abort)
10. apply dispute filter with findings as kept → done (kept=all, no disputes)
11. generate review report from kept as report → done
12. return report as review_report → done (section A)

Gates and outcomes:
- require target exists: PASS
- verify every finding has quoted evidence: PASS (no discard/abort)
- require confirmation: assumed PASS headless; otherwise-path "Dismissed; nothing changed." not taken

WOULD-ASK items:
- WOULD-ASK 1: which findings to dispute (as `disputed`)? Headless default: none disputed.
- WOULD-ASK 2 (implicit in require confirmation): confirm to finalize report? Headless default: confirmed.

Skipped:
- Nothing skipped. No failure-path aborts triggered. No code modifications (forbidden by contract).
