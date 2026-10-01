(A) FULL REVIEW REPORT

# Code Review: File-share API — upload handling, tokens, and user lookup (target2.py)

## Summary

This file implements file-share upload handling, token generation, user registration, and role-gated file listing; overall it is not mergeable in its current state due to multiple exploitable security flaws and a shared-mutable-state bug.

**Verdict**: [ ] Approve | [x] Request Changes | [ ] Comment

> Note: No PR description was provided for this single-file review. Intent recap above is inferred from the module docstring and function names. Proceeding with best judgment per headless mode.
>
> Critical issues were identified in Step 3 (Details) and are flagged immediately below per workflow Step 5 — do not merge before fixing.

## Critical Issues (Must Fix)

### 1. [target2.py:13] Security: Command Injection via `shell=True`
- **Current**: `subprocess.run(f"scan {path}", shell=True)` with `path` derived from user-controlled `filename`
- **Suggested**: Never pass user input through shell; use argument list with `shell=False`
- **Impact**: Remote command execution — `filename="x; rm -rf /"` or `$(...)` executes arbitrary commands (OWASP A03 Injection)

```python
# Current (vulnerable)
subprocess.run(f"scan {path}", shell=True)

# Suggested (secure)
import shlex
subprocess.run(["scan", path], shell=False, check=True, timeout=30)
```

### 2. [target2.py:10-11] Security: Path Traversal / Unrestricted File Write
- **Current**: `path = f"uploads/{filename}"` with no sanitization
- **Suggested**: Basename + allowlist + join + containment check
- **Impact**: Arbitrary file overwrite — `filename="../../app.py"` or absolute paths escape `uploads/` (OWASP A01 Broken Access Control / A04 Insecure Design)

```python
# Current (vulnerable)
path = f"uploads/{filename}"

# Suggested (secure)
from pathlib import Path
UPLOAD_DIR = Path("uploads")
safe_name = Path(filename).name  # strip directories
if not safe_name or safe_name.startswith("."):
    raise ValueError("Invalid filename")
path = UPLOAD_DIR / safe_name
if path.resolve().parent != UPLOAD_DIR.resolve():
    raise ValueError("Invalid filename")
```

### 3. [target2.py:23] Security: Broken Password Hashing with Unsalted MD5
- **Current**: `hashlib.md5(request["pw"].encode()).hexdigest()`
- **Suggested**: Use a slow, salted password hasher (bcrypt / argon2 / scrypt)
- **Impact**: Fast, unsalted, collision-broken hash — passwords recoverable via rainbow tables / GPU cracking on DB leak (OWASP A02 Cryptographic Failures)

```python
# Current (vulnerable)
digest = hashlib.md5(request["pw"].encode()).hexdigest()

# Suggested (secure) — e.g. with bcrypt
import bcrypt
digest = bcrypt.hashpw(request["pw"].encode(), bcrypt.gensalt()).decode()
# Verify with bcrypt.checkpw(candidate.encode(), stored.encode())
```

### 4. [target2.py:17-18] Security: Predictable, Low-Entropy Token Unbound to User
- **Current**: `random.randint(100000, 999999)`; `user_id` argument ignored
- **Suggested**: Use `secrets` with ≥128 bits entropy and bind to user/expiry
- **Impact**: `random` is not CSPRNG; 6-digit space (~20 bits) is brute-forceable; token is not tied to `user_id`, allowing reuse across accounts (OWASP A02 Cryptographic Failures)

```python
# Current (vulnerable)
def make_token(user_id):
    return random.randint(100000, 999999)

# Suggested (secure)
import secrets
def make_token(user_id: int) -> str:
    return f"{user_id}:{secrets.token_urlsafe(32)}"
    # Persist + expire server-side; validate binding on use
```

### 5. [target2.py:30-32] Security: Caller-Controlled Authorization Check
- **Current**: `def list_files(db_path, role, ...)` then `if role == 2`
- **Suggested**: Derive role server-side from authenticated session, not a caller-supplied argument
- **Impact**: Any caller can pass `role=2` to dump the whole `files` table — authorization bypass (OWASP A01 Broken Access Control)

```python
# Current (bypassable)
def list_files(db_path, role, extra=[]):
    if role == 2:
        ...

# Suggested
def list_files(db_path, current_user) -> list:
    if current_user.role != Role.ADMIN:
        raise PermissionError("Admin required")
    ...
```

## Major Issues (Should Fix)

### 1. [target2.py:30] Logic: Mutable Default Argument `extra=[]`
- **Current**: `def list_files(db_path, role, extra=[])`
- **Suggested**: Use `None` sentinel
- **Impact**: Default list is shared across calls — if any caller mutates the returned `extra` or you later append, state leaks between requests

```python
# Current (buggy)
def list_files(db_path, role, extra=[]):

# Suggested
def list_files(db_path, role, extra=None):
    extra = list(extra) if extra is not None else []
```

### 2. [target2.py:21-22] Logic: Missing Input Validation / Null Checks
- **Current**: Direct `request["email"]`, `request["pw"]` with no presence, type, or format checks
- **Suggested**: Validate and fail fast with clear errors
- **Impact**: `KeyError` / `AttributeError` on malformed input; invalid emails stored; empty passwords accepted

```python
# Suggested
email = request.get("email", "").strip()
password = request.get("pw", "")
if not email or "@" not in email:
    raise ValueError("Valid email is required")
if len(password) < 8:
    raise ValueError("Password must be at least 8 characters")
```

### 3. [target2.py:24-26,31-33] Reliability: DB Connections Never Closed, No Error Handling
- **Current**: `sqlite3.connect(db_path)` with no `close()`, no `try/finally`, no handling of `IntegrityError` (duplicate email) or `sqlite3.Error`
- **Suggested**: Context manager + specific exception handling + logging
- **Impact**: Connection/file-descriptor leaks under load; duplicate registration crashes with raw traceback

```python
# Suggested
import sqlite3
try:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users (email, pw) VALUES (?, ?)",
            [email, digest],
        )
except sqlite3.IntegrityError:
    raise ValueError(f"Email already registered: {email}")
```

### 4. [target2.py:9] Logic: `username` Parameter Ignored — Missing Auth Binding
- **Current**: `handle_upload(username, filename, data)` never uses `username`
- **Suggested**: Either enforce ownership/quotas with it or remove it
- **Impact**: Uploads are unattributed; no per-user isolation, quota, or audit trail

```python
# Suggested (option A — enforce)
def handle_upload(username: str, filename: str, data: bytes) -> str:
    user = get_authenticated_user(username)  # verify caller identity
    ...
    log.info("upload", extra={"user": user.id, "file": safe_name})
```

### 5. Missing Tests — No Test Coverage Provided
- **Current**: Only `target2.py` supplied; no tests to review
- **Suggested**: Add tests asserting behavior for happy path, rejection paths, and security boundaries
- **Impact**: None of the critical paths (traversal rejection, injection safety, hashing, auth denial, mutable-default isolation) are verified

```python
# Suggested (examples)
def test_upload_rejects_traversal(tmp_path):
    with pytest.raises(ValueError):
        handle_upload("alice", "../../etc/passwd", b"x")

def test_list_files_does_not_share_default():
    a = list_files(":memory:", role=Role.USER)
    a.append("x")
    assert list_files(":memory:", role=Role.USER) == []
```

## Minor Issues (Nice to Have)

### 1. [target2.py:32] Maintainability: Magic Number `role == 2`
- **Current**: `if role == 2:`
- **Suggested**: Named constant / enum

```python
# Suggested
from enum import IntEnum
class Role(IntEnum):
    USER = 1
    ADMIN = 2
if role == Role.ADMIN:
    ...
```

### 2. [target2.py:18] Maintainability: Magic Numbers `100000, 999999`
- **Current**: `random.randint(100000, 999999)`
- **Suggested**: Named constants (and preferably replace with `secrets` per Critical #4)

```python
TOKEN_MIN = 100_000
TOKEN_MAX = 999_999
```

### 3. [target2.py:33] Maintainability: `SELECT *`
- **Current**: `conn.execute("SELECT * FROM files")`
- **Suggested**: Explicit column list; add pagination for large tables

```python
# Suggested
rows = conn.execute(
    "SELECT id, owner, filename, created_at FROM files LIMIT ? OFFSET ?",
    [limit, offset],
).fetchall()
```

### 4. [target2.py:3] Style: Unused Import `os`
- **Current**: `import os` is never referenced
- **Suggested**: Remove it (or use `os.path` / `pathlib` in the sanitized join)

### 5. [target2.py:9-14] Robustness: No Upload Limits or Error Handling
- **Current**: No size cap on `data`, no `UPLOAD_DIR` creation, no `OSError` / `subprocess` failure handling
- **Suggested**: Enforce `MAX_UPLOAD_BYTES`, `mkdir(parents=True, exist_ok=True)`, catch and log failures with a safe error to the caller

## Positive Feedback

- Great use of a parameterized query in `register()` (`VALUES (?, ?)` with bound parameters) — that is exactly the right defense against SQL injection; keep that pattern everywhere.
- Nice use of the `with open(...)` context manager for the file write in `handle_upload()` — deterministic cleanup on that path.
- Appreciate the small, single-purpose function decomposition (`handle_upload` / `make_token` / `register` / `list_files`) and the module docstring stating intent — it made the missing pieces easy to spot.

## Questions for Author

- What is the expected auth model? Should `username` / `role` come from a trusted session rather than caller arguments, and who is allowed to upload vs. list all files?
- What are the upload requirements — allowed file types, max size, and should the `scan` step block the response or run asynchronously? What should happen when the scan fails or times out?
- For tokens: expected format, lifetime, and single-use vs. reusable? Should they be persisted and revocable?
- For `register()`: expected behavior on duplicate email, and is there a password policy (min length, complexity) to enforce?

## Test Coverage Assessment

- [ ] Happy path tested (no tests supplied)
- [ ] Error cases tested (missing: duplicate email, bad input, scan failure, DB errors)
- [ ] Edge cases tested (missing: traversal filenames, empty data, oversized upload, `extra` isolation)
- [ ] Security boundaries tested (missing: shell metachars in filename, role bypass, token unpredictability)
- [ ] Integration tests present

## Checklist

- [ ] No security vulnerabilities (command injection, traversal, MD5, weak tokens, auth bypass)
- [ ] Performance is acceptable (unbounded `fetchall()` + `SELECT *`, no pagination)
- [x] Code is small and readable
- [ ] Tests are adequate (none supplied)
- [ ] Documentation is present (module docstring only; no API/contract docs)
- [ ] Error handling is adequate
- [ ] Resource cleanup is correct (DB connections leak)

---

(B) META

- Skill: `code-reviewer` v1.1.0 (`/mnt/z/skilldesigner/test/bench/skill-orig/SKILL.md`); target: `/mnt/z/skilldesigner/test/bench/target2.py` (single-file review, no PR).
- Workflow steps followed:
  1. Context — noted missing PR description; inferred intent from module docstring; wrote one-sentence recap.
  2. Structure — assessed decomposition, auth model, abstraction fit; flagged caller-supplied identity/role as architectural concern.
  3. Details — applied Reference Guide checks (OWASP Top 10 baseline, injection, crypto, validation, N+1/secrets scan, common-issues patterns); surfaced 5 criticals immediately.
  4. Tests — reviewed test coverage (none supplied) as thoroughly as code; specified missing behavior assertions.
  5. Feedback — produced categorized report per Output Template + Report Template with code examples, prioritization, praise, questions, verdict.
- Checkpoints/gates hit:
  - Step 1 checkpoint: one-sentence intent summary (done, inferred; flagged as uncertain due to no PR description).
  - Step 3 gate: N+1 / hardcoded secrets / injection scan (done — injection found, no N+1 applicable, no hardcoded secrets found).
  - Step 5 gate: criticals noted immediately (done — called out at top of report).
  - Report-template pre-submit checks: criticals have remediation, majors state impact, ≥1 praise included, questions specific/answerable, verdict matches issues (Request Changes).
  - Spec-compliance Stage 1 → Stage 2 ordering: attempted Stage 1, blocked on missing spec/PR (recorded below), proceeded to Stage 2 with best judgment.
- WOULD-ASK items (headless; continued with best judgment):
  1. (Step 1) Ask author to clarify PR intent / link issue-ticket — no description exists.
  2. (Step 2) Ask whether caller-passed `username`/`role` is intentional or should come from session auth.
  3. (Step 3) Ask about upload contract (file types, size limits, scan failure semantics).
  4. (Step 3) Ask about token contract (format, entropy, lifetime, persistence/revocation).
  5. (Step 4) Ask where tests live / whether to require new tests asserting behavior not implementation.
  6. (Spec compliance) Ask for original requirements to verify missing/unnecessary/interpretation gaps.
- Reference files loaded (5/6):
  - `references/review-checklist.md` (starting a review — categories, process)
  - `references/common-issues.md` (N+1, magic numbers, patterns)
  - `references/feedback-examples.md` (writing good feedback)
  - `references/report-template.md` (writing final review report)
  - `references/spec-compliance-review.md` (PR review / spec verification ordering)
- Skipped:
  - `references/receiving-feedback.md` — applies to responding to review comments, not giving a review; not applicable to this direction.
  - Full spec-compliance verification (missing/unnecessary/interpretation-gap line-by-line) — skipped because no spec, ticket, or PR description exists to verify against; recorded as limitation instead of inventing requirements.
  - Style nitpicks / linter-gated formatting blocks — skipped per Disagreement handling (never block on style when a linter/formatter may own it; none confirmed here).
