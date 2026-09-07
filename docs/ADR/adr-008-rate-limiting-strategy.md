# ADR-008: Client-Side Resilience, Rate Limiting, and Error Handling

*   **Status:** Approved
*   **Deciders:** ARus
*   **Date:** 2026-09-04 UTC

---

## 1. Context and Problem Statement

In Sprint 1, the client executed simple synchronous HTTP calls and immediately raised exceptions on any server-side error or 429 status code. 

With Sprint 4 expanding the scope to support 12 distinct read-only resource endpoints, request density will increase dramatically—especially when performing nested listings or full resource synchronizations. 

If we attach independent rate-limit trackers to each of the 12 endpoints, we create separate request allowances, which makes it extremely easy to overwhelm the mock API. Furthermore, handling transient failures (like network blips, database lockouts, or rate limits) in a scattered, ad-hoc manner across every endpoint leads to massive code duplication and inconsistent retry tracking.

We need a unified, thread-safe, and deterministic resilience design at the shared client boundary to govern rate limiting, retries, and correlation logging.

---

## 2. Decision Outcomes and Technical Specifications

We will centralize all resilience, backoff, and exception logic at the shared `SimproClient` transport request layer. This guarantees a single coordinated policy for all 12 endpoints.

### 2.1. Lock-Protected Token Bucket Limiter
*   **Component Location:** `src/simpro_client/rate_limiter.py`
*   **Behavioral Strategy:** Every outgoing request must pass through a single thread-safe `token bucket` limiter attached to the client instance.
*   **Parameters:** Configurable via `.env` and loaded by `config.py`:
    *   `SIMPRO_LIMITER_CAPACITY` (Default: `8`)
    *   `SIMPRO_LIMITER_REFILL_RATE` (Default: `8.0` tokens/sec)
*   **Thread Safety Lock-Release Rule:** A standard threading lock is acquired to perform the token arithmetic (time elapsed, tokens added/consumed). Crucially, **the lock must be released before any sleep/wait delay occurs**. This prevents blocking unrelated client requests that could run without delaying.

### 2.2. Isolated Retry Budgets (401 vs 429)
*   To prevent cascading failure and retry exhaustion, authentication recovery and rate-limiting recovery must run on completely independent budgets:
    1.  **401 Unauthorized Invalidation:** When a 401 is encountered, the client performs a one-time token refresh attempt. If this attempt fails, it raises an exception immediately.
    2.  **429 Too Many Requests:** When a 429 is encountered, the client enters a dedicated rate-limit retry loop governed by `SIMPRO_MAX_RETRIES` (Default: `3`).
*   **Execution Order:** If a single logical request returns a 401 (reloads token) and subsequently encounters a 429 on retry, the rate-limiting loop must start with its full, untouched retry budget.

### 2.3. Retry-After Header Precedence
When a 429 status code is received, the client must evaluate and honor the server's cooldown recommendation:
1.  **Header Check:** Read the `Retry-After` header. It must support both integer/decimal delay seconds (e.g., `5` or `2.5`) and standard HTTP-date formats.
2.  **Precedence:** If a valid header value is found, the client sleeps for that exact duration.
3.  **Fallback:** If the header is missing, malformed, or negative, the client falls back to a bounded `exponential backoff with jitter` formula (e.g., $t = 2^{attempt} \times \text{jitter}$).

### 2.4. Stable Correlation ID Propagation
*   To enable end-to-end tracing across retries and backend logs, a single `correlation ID` must be maintained.
*   The correlation ID is retrieved from the thread-safe `ContextVar` on the first attempt and sent via the `X-Correlation-ID` header.
*   **Retention Rule:** Every retry attempt under that logical execution must reuse the **exact same** correlation ID. Generative steps for new correlation IDs must never trigger during retries.
*   All logs and raised exceptions resulting from these requests must contain this active correlation value.

### 2.5. Unified, Rich Error Hierarchy (`src/simpro_client/exceptions.py`)
We expand our exception hierarchy to give callers rich diagnostic metadata:
*   `SimproError` (Base Exception)
    *   `SimproClientError` (For all 4xx responses; exposes `method`, `url`, `status_code`, `response_body`, and `correlation_id`)
        *   `SimproRateLimitError` (For 429 responses; extends client-error with `retry_after` and `attempt_count` fields)
    *   `SimproServerError` (For 5xx responses; exposes server error details)
    *   `SimproProtocolError` (For malformed data types or failed pagination schemas)

---

## 3. Verification and Acceptance Gates

To guarantee robust execution and prevent code regressions, the developer must prove compliance using two verification gates:

### 3.1. Offline Deterministic Unit Tests
The resilience and retry paths must be verified in complete isolation under `tests/test_rate_limiter.py` and `tests/test_retries.py`:
*   **Time Control:** Tests must mock/inject the system clock, sleeping mechanism, and random jitter to avoid real-time delays during testing.
*   **Mock Network Routing:** Use `RESPX` sequential routing to stub the mock responses (e.g., first returning a 429 with `Retry-After: 1.5`, then returning a 200).
*   *Assert:* Test runs must complete in milliseconds, confirming retry limits, headers, and token buckets work perfectly without executing active sleeps or external sockets.

### 3.2. Static Quality Inspection
The modified files must cleanly clear the linter and format gates:
```bash
ruff check src/simpro_client/rate_limiter.py src/simpro_client/client.py src/simpro_client/exceptions.py
ruff format --check src/simpro_client/rate_limiter.py src/simpro_client/client.py src/simpro_client/exceptions.py
```

---

## 4. Architectural Alternatives Considered

*   **Endpoint-level Rate Limiting:** Rejected because treating each endpoint as an independent silo allows concurrent lists to overload the server, violating the single mock boundary rule.
*   **Thread-Block Sleeping (Lock Held):** Rejected because holding the thread-safety lock during a rate-limit sleep blocks other active client loops on different threads from calculating tokens, unnecessarily bottlenecking concurrent execution.
