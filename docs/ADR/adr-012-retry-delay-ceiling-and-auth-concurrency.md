# ADR-012: Retry Delay Ceiling and Token-Refresh Concurrency

*   **Status:** **Accepted (2026-10-06, ARus).** Supersedes ADR-010 §2.3 and
    extends ADR-010 §2.1. Drafted 2026-10-06 by Claude at ARus's request.
*   **Deciders:** ARus
*   **Date:** 2026-10-06 UTC
*   **Context/Phase:** Phase 3, `simpro_client`
*   **Relates to:** ADR-005 (auth strategy), ADR-007 (configuration),
    ADR-010 (resilience policy), ADR-011 (exception hierarchy).
    If accepted, supersedes ADR-010 §2.3 and extends ADR-010 §2.1.

---

## 1. Context

An audit of the retry pipeline on 2026-10-06 found two gaps between what
ADR-010 promises and what `client.py` and `auth.py` actually do. Both were
reproduced against the code as it stands on `develop`.

`docs/CLAUDE.md` §4 forbids editing the Decision of an Approved ADR, so the
correction is recorded here rather than as an amendment to ADR-010.

### 1.1 `Retry-After` is honoured without an upper bound

ADR-010 §2.3.2 says the client "halts execution for that exact duration".
`SimproClient._retry_delay()` implements this literally: it returns the
parsed header verbatim. The `min(60, ...)` ceiling in `_backoff_delay()`
applies **only** to the fallback path, so a server-supplied delay is never
bounded. Measured end to end through `client.get()`:

| `Retry-After` | Result |
|---|---|
| `86400` | `time.sleep(86400.0)` — the calling thread blocks for 24 hours |
| `Fri, 01 Jan 2100 00:00:00 GMT` | `time.sleep(2311145768.8)` — about 73 years |
| `99999999999999999999` | `OverflowError: timestamp out of range for platform time_t`, uncaught |

The third case escapes the public API as a non-`SimproError`, which ADR-011
and `src/simpro_client/CLAUDE.md` §6 forbid. The path is reachable from a 429
and, through `_retry_delay`, from 502/503/504.

This is not a deviation from ADR-010. The code complies with §2.3.2 as
written; the hazard is in the policy. §2.3.3 also calls the fallback
"bounded" while giving a formula with no bound.

### 1.2 `AuthManager` is not thread-safe

ADR-010 §1 calls for a "thread-safe" architecture and §3 claims "zero
deadlock behavior in multithreaded workers". `TokenBucket` holds a
`threading.Lock`; `AuthManager` holds none, and mutates `_access_token` and
`_token_expiry` without synchronisation.

Measured with eight threads calling `get_token()` concurrently against a
50 ms token endpoint: **eight** token requests, where a serialised refresh
gives one. Each also draws a limiter token, so a herd can drain the whole
default bucket (capacity 8) on token traffic alone. Separately, a 401 in one
thread calls `invalidate()`, which can blank a token another thread has just
fetched, forcing a further redundant refresh.

No deadlock and no crash was observed. The cost is wasted token traffic and
wasted rate budget.

---

## 2. Options

### 2.1 Delay ceiling

Where the clamp goes is not a free choice. `_parse_retry_after()` has two
call sites: `client.py:288` computes the sleep, but `client.py:246` builds
`SimproRateLimitError(retry_after=...)`. Clamping inside the parser was
measured to change the reported value from `86400.0` to `60.0` — the client
would tell the caller the server asked for 60 s when it asked for a day. Any
option below therefore clamps in `_retry_delay()` and leaves the parser as
the honest reporter of what the server sent.

- **A1 — Clamp to the existing hardcoded 60 s.** Smallest change. The client
  then retries *earlier* than the server permitted, spending retry budget on
  traffic the server has already refused.
- **A2 — Clamp to a configurable ceiling.** As A1, with
  `SIMPRO_MAX_RETRY_DELAY` (default `60.0`) added per ADR-007. Same
  early-retry behaviour, tunable per deployment.
- **A3 — Ceiling as a retry cut-off.** If the parsed `Retry-After` exceeds
  the ceiling, do not sleep and do not retry: raise at once, carrying the
  true uncapped value. Below the ceiling, honour the header exactly, as
  today.
- **A4 — Leave as is and record the hazard in `known-issues.md`.**

Under every option the fallback backoff keeps its existing ceiling, and the
`OverflowError` handler proposed during review is **not** added: once every
delay is capped, `time.sleep()` can never receive an unsleepable value, so
the handler would be unreachable code, which the root `CLAUDE.md` §5 forbids.
The clamp is the `OverflowError` fix.

**Recommendation (non-binding — for CVC's decision): A2.**

There is no live Simpro API access (root `CLAUDE.md` §1), so we cannot know
whether the real API ever sends a large `Retry-After`. Under that
uncertainty A2 fails soft: a misconfigured header costs three refused
requests and about 180 s at the default ceiling, and the call still
completes if the server relents. A3 fails hard and loses a sync pass that
might have succeeded. Making the ceiling a setting means the trade can be
revisited per deployment without a code change.

A3 becomes the better option if we learn that Simpro uses a large
`Retry-After` deliberately to signal quota exhaustion, because retrying
early would then be both futile and potentially ban-extending. A4 is
rejected: an unbounded sleep with no log line is not a defect we should
carry into Phase 4.

### 2.2 Token-refresh concurrency

- **B1 — Double-checked `threading.Lock` in `AuthManager`.** The fast path
  reads the cached token with no lock; on a miss, take the lock, re-check,
  and refresh only if still stale. `invalidate()` takes the same lock.
  Collapses the herd to one request. Standard library, no new dependency.
- **B2 — Token-aware `invalidate(token=...)`.** A refinement on top of B1:
  the client passes the token that received the 401, and the cache is
  cleared only if it still holds that token, so a late 401 cannot discard a
  newer token. The value is already in scope at `client.py:239`. The
  parameter is optional, so existing calls keep working.
- **B3 — `threading.RLock` instead of `Lock`.** No re-entrant path exists
  today: `_get_oauth_token()` takes the lock and calls `_refresh_token()`,
  which never re-acquires, and `invalidate()` is never called from inside a
  locked section. `RLock` costs nothing but would silently permit a future
  recursive acquire that a plain `Lock` surfaces immediately in testing.
- **B4 — Declare the client single-threaded per instance** and withdraw
  ADR-010's thread-safety claim.

**Recommendation (non-binding — for CVC's decision): B1 with B2.**

B1 is about fifteen lines and closes the gap against a claim ADR-010 already
makes. B2 is four more and removes the last redundant-refresh path. B3 is a
reasonable safety margin if preferred; the recommendation is `Lock` only
because a hang in a test is a better failure than a silent recursive
acquire. B4 is rejected: it contradicts the deliberately lock-protected
`TokenBucket` and the shared-client design in ADR-010 §2.1.

---

## 3. Decision

Accepted 2026-10-06 by ARus:

- **§2.1 — Option A2.** The clamp lives in `_retry_delay()` and is bounded
  by a new `SIMPRO_MAX_RETRY_DELAY` setting (default `60.0`).
  `_parse_retry_after()` stays uncapped, so
  `SimproRateLimitError.retry_after` keeps reporting the value the server
  actually sent. No `OverflowError` handler is added, because the clamp
  makes that branch unreachable.
- **§2.2 — Options B1 and B2.** A double-checked `threading.Lock` in
  `AuthManager`, together with token-aware `invalidate(token=...)`.
  `RLock` (B3) was considered and not chosen.

---

## 4. Consequences

*   **Positive:** Any single logical call is bounded by
    `max_retries × max_retry_delay` of sleeping, instead of being unbounded.
*   **Positive:** No non-`SimproError` can escape the retry path, restoring
    the ADR-011 guarantee.
*   **Positive:** The caller still learns the server's true cooling-off
    period through `SimproRateLimitError.retry_after`; the value is bounded
    for sleeping, not for reporting.
*   **Positive:** Token traffic under concurrency drops from N requests to
    one, freeing the limiter budget the herd was consuming.
*   **Negative:** The client may now send a request before the server's
    stated cooling-off period has elapsed. This is the accepted cost of A2
    over A3, and `SIMPRO_MAX_RETRY_DELAY` is the lever if it proves wrong.
*   **Negative:** B1 holds the auth lock across the token request, so during
    a refresh other threads block for up to `SIMPRO_TIMEOUT` (default 30 s)
    plus any limiter wait. That is the intent — they would otherwise each
    issue their own request — but it is a new blocking window.
*   **Deadlock analysis:** `_refresh_token()` acquires the limiter while
    holding the auth lock, so the order is auth-lock then bucket-lock.
    `TokenBucket` never calls into `AuthManager`, so the reverse order does
    not exist and no cycle is possible. `TokenBucket.acquire()` already
    sleeps outside its own lock (`rate_limiter.py:43`), so the bucket lock is
    never held across a wait.
*   **Scope limit:** this makes `AuthManager` thread-safe. `httpx.Client` is
    thread-safe, and the endpoint classes hold no mutable state beyond
    `self._client`, set in `__init__` (`endpoints/base.py:38`; verified by
    inspection, not by a stress test). Whole-client thread-safety is
    therefore plausible but is neither claimed nor tested by this ADR.

---

## 5. Out of scope

The same audit found that `get_correlation_id()` writes its generated ID
back into the `ContextVar` and nothing clears it, so every call in a thread
shares one correlation ID and two logical calls cannot be told apart in
logs. That is an observability gap, not a safety one, and the likely fix
(a distinct per-request ID alongside the existing correlation ID) adds a
field rather than changing a decision ADR-010 §2.4 records. It is therefore
handled as a separate change, not here.

The decimal `Retry-After` deviation already recorded in
`src/simpro_client/CLAUDE.md` is unrelated and unchanged by this ADR.

---

## 6. Follow-up on acceptance (done 2026-10-07)

Implemented on branch `docs/adr-012-retry-delay-ceiling`:

- `0c80cf7` — §2.1 (A2). `_retry_delay()` caps the parsed `Retry-After` at
  the new `max_retry_delay` setting; `_backoff_delay()` reads the same
  setting; `_MAX_RETRY_DELAY_SECONDS` removed. `SIMPRO_MAX_RETRY_DELAY`
  added to `config.py` and `.env.example`.
- `2404bf4` — §2.2 (B1 and B2). `AuthManager._lock`, double-checked in
  `_get_oauth_token()`; `invalidate(token=None)`; `client.py` passes the
  rejected token.

Measured outcomes:

- `Retry-After: 86400` now sleeps 60.0 s, not 86400.0 s. An HTTP-date in
  2100 now sleeps 60.0 s, not 2311145768.8 s.
  `Retry-After: 99999999999999999999` returns normally instead of raising
  `OverflowError` out of `client.get()`.
- `SimproRateLimitError.retry_after` still reports `86400.0`.
- Eight concurrent `get_token()` calls now make 1 token request, not 8.
- The mixed-recovery trace is unchanged: three attempts, two token fetches,
  one stable correlation ID, independent budgets.
- Offline suite 90 passed, 2 deselected (was 81). No new ruff violations.

Documents updated in the same commits: `src/simpro_client/CLAUDE.md`,
`docs/architecture.md`, `docs/CHANGELOG.md`, `docs/README.md` §3 and §5,
root `CLAUDE.md` §4, `docs/ADR/ADR-index.md`, `adr-010`'s Status line,
`tests/CLAUDE.md` §2 and `structure.txt`.

---

## 7. Verification

- `tests/test_retries.py`: an over-ceiling `Retry-After` sleeps the ceiling,
  not the header value; `SimproRateLimitError.retry_after` still reports the
  true uncapped value; `Retry-After: 99999999999999999999` is capped like
  any other over-ceiling value, so the retry proceeds normally and no
  `OverflowError` can reach `time.sleep()`; a below-ceiling value and the
  fallback backoff behave exactly as today; the transient-5xx path is
  bounded the same way.
- `tests/test_auth.py`: concurrent `get_token()` calls produce exactly one
  token request; `invalidate(token=...)` does not clear a newer token.
- The mixed-recovery trace (401, then 429, then 200) is unchanged: three
  attempts, two token fetches, one stable correlation ID, independent
  budgets.
- `uv run pytest -q -m "not integration"`. Baseline before this change is
  81 passed, 2 deselected.
