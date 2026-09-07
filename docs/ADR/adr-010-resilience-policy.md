# ADR-010: Client-Side Resilience, Rate Limiting, and Error Handling

*   **Status:** Approved
*   **Deciders:** ARus
*   **Date:** 2026-09-07 UTC
*   **Context/Phase:** Phase 3 / Sprint 4 Implementation

---

## 1. Context and Problem Statement

In Sprint 1, the core synchronous HTTP client was designed with basic request/response flows. If a 429 (Too Many Requests) or a transient network disruption occurred, the client immediately raised an exception, relying on caller-side application logic to catch and recover.

In Sprint 4, the system is scaling to support twelve distinct read-only resource endpoints. Because resource retrieval is nested (e.g., querying site-scoped assets, customer-scoped contacts, or job-scoped notes), a single synchronization pass will trigger a high density of downstream requests. 

If endpoints manage their own independent rate-limiting states, we risk over-allocating requests, causing rate-limiting starvation or backend service exhaustion. Furthermore, handling transient errors (like 429 status codes, 503 gateway outages, or socket timeouts) in an ad-hoc manner across all twelve modules introduces massive code duplication and compromises trace consistency.

We need a centralized, thread-safe, and highly predictable resilience architecture managed strictly at the shared client transport boundary.

---

## 2. Decision Outcomes and Technical Specifications

We will establish a unified resilience and error boundary directly on the `SimproClient` transport layer (inside `src/simpro_client/client.py`). This guarantees that all twelve endpoint modules share a single resilience policy, token budget, and diagnostic trace loop.

### 2.1. Shared Lock-Protected Token Bucket Limiter
*   **Location:** `src/simpro_client/rate_limiter.py`
*   **Mechanism:** Every outbound transport execution must pass through a single, client-instance-wide `token bucket` rate limiter.
*   **Configuration:** 
    *   `SIMPRO_LIMITER_CAPACITY` (Default: `8` tokens)
    *   `SIMPRO_LIMITER_REFILL_RATE` (Default: `8.0` tokens/second)
*   **Lock Release Concurrency Guard:** A threading lock is acquired solely to compute elapsed token accumulation and deduct tokens. Crucially, **the lock must be released before any rate-limiting sleep/wait begins**. This ensures that thread-pools can queue and calculate rates concurrently without suffering lock-block starvation.

### 2.2. Isolated Recovery Budgets (401 vs 429)
To prevent retry-loop exhaustion and cascading failure states, authentication tokens and transient network/rate limits operate on separate budgets:
1.  **401 Unauthorized Recovery:** If a request encounters a 401, the client executes a single, isolated token refresh handshake. If the refresh fails or the subsequent retry also returns a 401, the client exits immediately, raising a `SimproClientError`.
2.  **429/Transient Error Recovery:** Outbound requests are governed by a separate retry loop bounded by `SIMPRO_MAX_RETRIES` (Default: `3`).
*   **Precedence Order:** If a request triggers a 401 (refreshing the token) and then immediately encounters a 429 on the refreshed attempt, the rate-limiting retry loop starts fresh with its full, unconsumed retry budget.

### 2.3. Retry-After Header Compliance
When a 429 response is captured, the client must evaluate and defer to the server's requested cooling-off period:
1.  **Header Parsing:** Read the `Retry-After` header. It must accommodate both standard integer/decimal delay seconds (e.g., `3` or `1.5`) and HTTP-date formats.
2.  **Execution:** If a valid positive interval is parsed, the client halts execution for that exact duration.
3.  **Fallback Strategy:** If the header is missing, malformed, or negative, the client falls back to a bounded `exponential backoff with jitter` algorithm:
    $$\text{delay} = 2^{\text{attempt}} \times (0.5 + \text{random\_jitter})$$

### 2.4. Traceable Correlation ID Propagation
To ensure developer tracing capability across multi-attempt requests:
*   A single `correlation ID` is fetched from a thread-safe `ContextVar` at the beginning of the logical request and injected via the `X-Correlation-ID` header.
*   **Trace Retention Rule:** Every retry attempt under that logical execution block must carry the **exact same** correlation ID. Generative steps for fresh correlation IDs must never trigger during retry loops.
*   All intermediate warning logs, rate-limiting notifications, and final raised exceptions must retain and expose this active correlation ID.

### 2.5. Rich, Typed Exception Classification (`exceptions.py`)
Our error hierarchy is extended to offer deep debugging telemetry without breaking backward compatibility:
*   `SimproError` (Base Client Exception)
    *   `SimproClientError` (For 4xx status codes; exposes `method`, `url`, `status_code`, `response_body`, and `correlation_id`)
        *   `SimproRateLimitError` (For 429 responses; extends client error with `retry_after` and `attempt_count`)
    *   `SimproServerError` (For 5xx status codes; exposes standard system errors)
    *   `SimproProtocolError` (For malformed pagination boundaries or API data validation mismatches)

---

## 3. Consequences and System Impact

*   **Positive:** Single, centralized implementation reduces code complexity across all 12 endpoints.
*   **Positive:** Concurrency lock separation guarantees high performance and zero deadlock behavior in multithreaded workers.
*   **Positive:** Strict separation of auth vs. rate-limiting retry budgets guarantees predictable exit states under network failure.
*   **Negative:** Adds slight processing latency to outgoing transport calls due to locking/validation checks, which is negligible compared to standard network roundtrips.

---

## 4. Verification and Acceptance Gates

To guarantee compliance, the implementing developer must satisfy two automated test gates:

### 4.1. Deterministic Mock-Time Unit Testing
All token bucket depletion, retry loops, and jitter behaviors must be tested in absolute isolation within `tests/test_rate_limiter.py` and `tests/test_retries.py`:
*   Tests must inject mock clocks or monkeypatch `time.sleep` to bypass physical delays.
*   Use `RESPX` sequence stubs to orchestrate mock status flows (e.g., mock responding with `429` on attempt 1, and `200 OK` on attempt 2).
*   Test execution must complete in milliseconds.

### 4.2. Quality Gate Passing
All modified files must pass static formatting checks with zero errors:
```bash
ruff check src/simpro_client/rate_limiter.py src/simpro_client/client.py
ruff format --check src/simpro_client/rate_limiter.py src/simpro_client/client.py
```
