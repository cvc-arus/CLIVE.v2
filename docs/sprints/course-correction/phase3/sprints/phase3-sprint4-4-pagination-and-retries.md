> Historical record as of 2026-09-29, commit 7094e0d. Not maintained.

# CLIVE-I HTTP Client: Resilience, Pagination, and Retries Upgrade

This repository houses the hardened, production-grade Python SDK for the Simpro API (code-named **CLIVE-I**). It introduces lazy, type-safe multi-page iteration, a thread-safe token bucket rate limiter, a centralized synchronous request recovery loop with independent budgets, and a robust typed exception hierarchy.

All upgrades are layered strictly on top of existing client features to maintain 100% backward compatibility with raw JSON-returning endpoints and synchronous page-by-page fetching.

---

## Architectural & Design Boundaries

To guarantee zero regression across upstream callers, this upgrade freezes several critical compatibility boundaries:
1. **Preserving `fetch_page()`:** Callers relying on immediate, raw single-page responses face no disruption.
2. **Preserving Raw JSON Methods:** Existing public client methods that return deserialized JSON payloads remain fully available.
3. **One Synchronous Transport Boundary:** The `SimproClient` continues to use a synchronous HTTPX backend, avoiding async rewrites.
4. **Offline Isolation:** Real API endpoints are never contacted during testing; the entire suite uses mock network definitions via `RESPX`.
5. **No Docker Dependencies:** Environment runtime constraints are managed locally via `uv`.

---

## Core Upgrades

### 1. Lazy Multi-Page Iteration (`iter_all`)
Every resource endpoint inheriting from `ResourceEndpoint` now exposes a lazy generator method:
```python
def iter_all(
    self,
    *,
    company_id: int | None = None,
    page_size: int = 30,
    filters: Mapping[str, FilterValue] | None = None,
    **scope_ids: int
) -> Iterator[ModelT]:
```
* **Deferred Evaluation:** No network requests are dispatched until the caller consumes the first element of the iterator.
* **Strict Validation:** Each page's items are parsed into Pydantic models in order. The generator validates pagination headers (`Result-Pages`) to reject missing, malformed, or contradictory metadata (e.g., zero pages, exceeding page boundaries, or unexpected premature empty pages) with a typed `SimproProtocolError`.

### 2. Thread-Safe Token Bucket (`TokenBucket`)
Rate limiting is controlled by a centralized, thread-safe token bucket integrated into the synchronous transport boundary:
* **Immediate Burst Capacity:** The bucket starts fully populated to permit immediate burst processing.
* **Sleeper Optimization:** Wait delays are calculated under a lock, but the thread sleeps outside the lock to prevent blocking concurrent threads.
* **Injected Timing:** The limiter allows injecting mock clock and sleeper callables, enabling 100% deterministic arithmetic assertions in tests without real-world latency.

### 3. Synchronous Recovery Loop & Independent Budgets
All requests route through a single, clean `while True` loop inside `_request_response`:
* **Correlation Tracing:** A stable `X-Correlation-ID` header is generated once at request initiation and preserved across all subsequent retries.
* **Authentication Budget:** A `401 Unauthorized` triggers token invalidation and refreshes the bearer token exactly once per request.
* **Rate-Limit Budget:** A `429 Too Many Requests` parses `Retry-After` (integer seconds or HTTP-date formats) and performs backoff up to `max_retries`.
* **Independent Budgets:** A single request sequence can consume both budgets (e.g., a 401 followed by a 429) without exhausting each other's retry limits.

### 4. Robust Exception Hierarchy
The error hierarchy is refined to give callers granular control:
* `SimproError`: Root library exception.
  * `SimproAuthError`: Authentication manager failures.
  * `SimproProtocolError`: Malformed or missing header contracts.
  * `SimproAPIError`: Root HTTP response error.
    * `SimproServerError`: Status `5xx` errors.
    * `SimproClientError`: Status `4xx` non-rate-limit errors.
      * `SimproNotFoundError`: Status `404` errors.
      * `SimproRateLimitError`: Status `429` errors (includes `retry_after`, `attempt_count`, and `retry_count` parameters).

---

## Configuration & Environment

The rate limiter defaults can be overridden via environment variables or a local `.env` file:

```ini
SIMPRO_BASE_URL=http://simpro-mock:8000/api/v1.0
SIMPRO_TOKEN_URL=http://simpro-mock:8000/oauth2/token
SIMPRO_CLIENT_ID=your-client-id-here
SIMPRO_CLIENT_SECRET=your-client-secret-here
SIMPRO_AUTH_MODE=client_credentials
SIMPRO_MAX_RETRIES=3
SIMPRO_LIMITER_CAPACITY=8
SIMPRO_LIMITER_REFILL_RATE=8.0
```

These values are automatically parsed and validated using Pydantic Settings under `SimproSettings` in `src/simpro_client/config.py`.

---

## Directory Structure

```text
├── .env.example
├── pyproject.toml
├── src/
│   └── simpro_client/
│       ├── __init__.py
│       ├── auth.py
│       ├── client.py
│       ├── config.py
│       ├── exceptions.py
│       ├── logging.py
│       ├── rate_limiter.py
│       └── endpoints/
│           ├── __init__.py
│           └── base.py
└── tests/
    ├── test_auth.py
    ├── test_client.py
    ├── test_endpoints.py
    ├── test_models.py
    ├── test_pagination.py
    ├── test_rate_limiter.py
    └── test_retries.py
```

---

## Testing & Quality Gates

To run development testing, synchronize your local environment first:
```bash
uv sync
```

### Focused Suites
Prove individual behaviors and units:
```bash
# Pagination tests (deferred execution, validation metadata)
uv run --locked pytest tests/test_pagination.py

# Rate Limiter tests (burst, lock release outside sleep)
uv run --locked pytest tests/test_rate_limiter.py

# Retry behavior tests (budgets, Retry-After parsing, fallback delay)
uv run --locked pytest tests/test_retries.py
```

### Offline Quality Gate
Before creating any handoff review, run the complete suite, including full linting and formatting style compliance:
```bash
# Run all unit tests offline
uv run --locked pytest tests/test_models.py tests/test_endpoints.py tests/test_pagination.py tests/test_auth.py tests/test_logging.py tests/test_client.py tests/test_rate_limiter.py tests/test_retries.py

# Run static quality analysis
uv run --locked ruff check src tests
uv run --locked ruff format --check src tests
git diff --check
```

### Review Handoff Check
Ensure that the workspace baseline remains uncommitted by verifying Git status:
```bash
git status --short
git diff --stat
git rev-parse --verify HEAD
```