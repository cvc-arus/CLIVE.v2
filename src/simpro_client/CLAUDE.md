# CLAUDE.md — `src/simpro_client/` (library)

Complements the root `CLAUDE.md`. Applies to `src/simpro_client/`.
`src/simpro_client.egg-info/` is build output. Do not edit it.

## 1. Responsibility

`simpro_client` is the reusable, synchronous, typed Python client for the
Simpro REST API. It currently runs against `simpro_mock` and must later run
against real Simpro by configuration change alone. It is a library (ADR-006):
no web server, no service wrapper, no persistence, no caching.

It must stay independent of the mock:
- Never import `simpro_mock` or read its code or database.
- Never hardcode mock details (port 8100, `mock-access-token-simpro`, mock
  hostnames). These belong in configuration and test fixtures only.
- Never add behaviour that exists only to satisfy a mock quirk. If the mock
  differs from real Simpro, the mock is the thing to fix (see
  `services/simpro_mock/CLAUDE.md`).

## 2. Layout (as implemented)

```
SimproClient (client.py)
  ├─ AuthManager (auth.py)         OAuth2 client credentials, or static API key
  ├─ TokenBucket (rate_limiter.py) one per client instance
  ├─ endpoints/*.py                one ResourceEndpoint subclass per resource
  │    └─ endpoints/base.py        Page, ResourceEndpoint: get / fetch_page / iter_all
  ├─ models/*.py                   one Pydantic model per resource (SimproBaseModel)
  ├─ exceptions.py                 typed hierarchy
  ├─ config.py                     SimproSettings, get_settings() (lru_cache)
  └─ logging.py                    ContextVar correlation IDs, JSONFormatter
```

Public API is what `simpro_client/__init__.py` exports, plus the exception
classes in `simpro_client.exceptions` (they are not re-exported from the
package root; callers import them from `simpro_client.exceptions`). Adding to
it is a deliberate API change; removing from or renaming it is a breaking
change and needs Alex's approval.

There is no separate `pagination.py`. Pagination lives in `endpoints/base.py`.
Do not create `pagination.py` unless a task asks for it.

## 3. Configuration (`config.py`)

- `SimproSettings`: pydantic-settings, prefix `SIMPRO_`, `env_file=".env"`,
  `extra="ignore"` (required so it can share `.env` with Phase 2 keys).
- Always required: `base_url`, `token_url`.
- Required per `auth_mode`, enforced by a `model_validator(mode="after")`:
  `client_credentials` needs `client_id` and `client_secret`; `api_key` needs
  `api_key`. Fields the mode does not use may be left unset, and an empty
  value counts as unset. Misconfiguration raises `ValidationError` at
  construction rather than `SimproAuthError` at the first request.
- Optional with defaults: `api_key`, `auth_mode`, `company_id_service` (1),
  `company_id_projects` (2), `timeout`, `max_retries` (3),
  `max_retry_delay` (60.0), `limiter_capacity` (8),
  `limiter_refill_rate` (8.0).
- `auth_mode` is `Literal["client_credentials", "api_key"]`. An unrecognised
  value raises `ValidationError` when settings are constructed; it no longer
  falls through to the OAuth path.
- `company_id_service` / `company_id_projects` are **reserved**: no library
  code reads them (see §8). They record CVC's company mapping for callers and
  for Phase 4. Leave them in place; do not wire them into endpoint defaults
  without a task.
- Every new setting needs a type, a default only if a safe default exists, a
  `Field(description=...)`, and a matching entry in `.env.example`.
- `SimproClient(settings=...)` must keep accepting explicit settings, so
  callers and tests never need a `.env` file.

## 4. Authentication (`auth.py`, ADR-005)

- Default `auth_mode="client_credentials"`: form-encoded POST to `token_url`,
  token cached in memory, refreshed 60 s before `expires_in`.
- **Refreshes are serialised** by `AuthManager._lock` (ADR-012 §2.2).
  `_get_oauth_token()` reads the cache unlocked, then re-reads it under the
  lock before refreshing, so N concurrent callers make one token request
  between them. `_refresh_token()` is called only with the lock held, and
  acquires the shared limiter while holding it; `TokenBucket` never calls
  back into `AuthManager`, so the auth-then-bucket order cannot cycle.
  `api_key` mode mutates nothing and stays lock-free.
- `invalidate(token=None)` clears the cache only if it still holds
  `token`, so a late 401 cannot discard a newer token another thread just
  fetched. `client.py` passes the token that received the 401. Calling it
  with no argument still clears unconditionally.
- `auth_mode="api_key"`: static token from settings. `config.py` now
  guarantees `api_key` is set in this mode, so `_get_api_key_token()`'s
  `SimproAuthError` guard is unreachable via validated settings. It is kept
  as defence in depth; do not remove it without a task.
- **`client_id` / `client_secret` are `str | None` at the type level.** The
  `model_validator` in `config.py` guarantees they are non-empty whenever
  `auth_mode="client_credentials"`, which is the only mode that reaches
  `_refresh_token()`, so passing them into the token payload is safe at
  runtime and no narrowing is needed for correctness. The project configures
  no type checker (`pyproject.toml` dev group is pytest, respx, ruff,
  pytest-cov), so nothing flags this today. If one is ever added, expect
  `arg-type`/`reportArgumentType` on the `client_id` and `client_secret`
  entries of the `_refresh_token()` payload; narrow there (an `assert` or an
  explicit raise), not by widening the validator or retyping the fields.
- `invalidate(token=None)` forces a refresh. The client uses it on a 401,
  passing the token that was rejected, so the cache is cleared only if it
  still holds that token (see §4). If that refresh fails, the client raises
  `SimproAuthRefreshError`; a failure on the first token fetch still raises
  plain `SimproAuthError`.
- `SimproAuthError` carries optional `status_code` (the **token endpoint's**
  status; `None` for transport or configuration errors) and `method`, `url`,
  `correlation_id` of the API request that needed the token. `auth.py` sets
  `status_code`; `_request_response()` fills in the rest (ADR-011).
- `SimproClient` passes its `TokenBucket` to `AuthManager(settings,
  limiter=...)`, so each token POST acquires from the same budget as API
  calls (ADR-010 §2.1). API-key mode makes no token request.
- Tokens live in memory only. Never write them to disk or logs.
- Authorization Code Grant ("Log in with Simpro") is deferred. Do not add it
  without a new ADR.

## 5. HTTP transport (`client.py`)

- `SimproClient._request_response()` is the **single funnel** for all API
  traffic. Every request must go through it so that it gets the rate limiter,
  `Authorization` and `X-Correlation-ID` headers, timing/logging, retries and
  error mapping. Do not call `self._http` directly anywhere else.
- Use only the existing `httpx.Client` instances (the client's own and
  `AuthManager`'s). Do not create per-call clients or add `AsyncClient`.
- `get` / `post` / `patch` / `delete` return raw decoded JSON (or `None` on
  204) and are kept for backward compatibility. Their existence does **not**
  put write operations in scope.

Response handling, as implemented:

| Response | Behaviour |
|---|---|
| `httpx.TimeoutException` / `httpx.NetworkError` | GET: retry up to `max_retries` with backoff; then (and for other methods) `SimproAPIError(status_code=0)` |
| other `httpx.HTTPError` | `SimproAPIError(status_code=0)`, no retry |
| 401 | invalidate token, retry once (separate budget); failed refresh → `SimproAuthRefreshError`; second 401 → `SimproClientError` |
| 429 | retry up to `max_retries`; honour `Retry-After` capped at `max_retry_delay`, else backoff |
| 404 | `SimproNotFoundError` |
| other 4xx | `SimproClientError` |
| 502 / 503 / 504 | GET: retry up to `max_retries`; honour `Retry-After` capped at `max_retry_delay`, else backoff; then (and for other methods) `SimproServerError` |
| other 5xx | `SimproServerError`, no retry |
| 204 | `None` from the raw methods |

Retry details: `Retry-After` is parsed as **integer seconds** or an HTTP-date,
then capped at `max_retry_delay` (`SIMPRO_MAX_RETRY_DELAY`, default 60.0)
before sleeping, so no single response can block the calling thread
indefinitely (ADR-012 §2.1). `_parse_retry_after()` itself is uncapped, so
`SimproRateLimitError.retry_after` reports what the server actually sent.
If missing or unparseable, backoff is
`min(max_retry_delay, 2**n * (0.5 + random()))`.
The same correlation ID is reused on every attempt of one logical request.
A 401 refresh followed by a 429 does not consume the 429 budget.
429, transient 5xx and transient network errors share one `max_retries`
budget. Transient retries are GET-only (`_RETRYABLE_METHODS`), so a
non-idempotent request is never re-sent after a timeout or 5xx.

Known deviations from ADR-010 (report them; do not "fix" them without a task):
- Decimal `Retry-After` values (e.g. `2.5`) are treated as unparseable and
  fall back to backoff. ADR-010 says they should be honoured.

## 6. Exceptions (`exceptions.py`)

```
SimproError
├── SimproAuthError              (status_code of token endpoint, method, url,
│                                 correlation_id; ADR-011)
├── SimproProtocolError          (bad or missing pagination headers)
└── SimproAPIError               (status_code, response_body, method, url,
    │                             correlation_id, retry_count)
    ├── SimproClientError        4xx
    │   ├── SimproNotFoundError  404
    │   ├── SimproRateLimitError 429 (retry_after, attempt_count)
    │   └── SimproAuthRefreshError 401, refresh after a 401 failed;
    │                             also a SimproAuthError (multiple inheritance)
    └── SimproServerError        5xx
```

The hierarchy above is the one ADR-011 (Accepted) defines; it supersedes
ADR-010 §2.5, so the `SimproAPIError` layer is no longer a deviation.
`SimproAPIError.__init__` must call `super().__init__()` before setting its
attributes, or `SimproAuthError.__init__` resets them to `None` in
`SimproAuthRefreshError`.

New exceptions subclass the closest existing class. Raised API errors must
carry `method`, `url` and `correlation_id`. Do not raise bare `Exception`,
`ValueError` or `httpx` errors across the public API for HTTP or protocol
failures. (Missing route parameters currently raise `ValueError` from
`ResourceEndpoint._render`; that is existing behaviour.)

## 7. Models (`models/`)

- Every resource model subclasses `SimproBaseModel` (`extra="ignore"`,
  `validate_by_alias=True`, `validate_by_name=True`).
- Every field has an explicit PascalCase `alias` and a snake_case attribute.
- **Field names, types and required vs optional are governed by the vendored
  contract, `docs/contracts/simpro-openapi-v1-get-subset.json`** (ADR-013).
  `tests/test_spec_conformance.py` enforces it. The mock follows that contract
  too, so if a model and `services/simpro_mock/simpro_mock/schemas.py`
  disagree, the contract decides which one is wrong — report it rather than
  matching the mock.
  (Before ADR-013 this rule pointed at the mock's schemas and
  `docs/phase3/sprints/phase3-sprint4-contract.md`. That sprint report is a
  historical record and is no longer normative; do not rewrite it.)
- Dates are `datetime.date`; timestamps are `datetime.datetime`. Money is
  `Decimal`, because the spec constrains money to two decimal places.
- Do not add fields the contract does not document. Adding a field the contract
  documents but the mock does not yet serve is allowed and expected — that is
  how the re-shape proceeds — but it must be optional until the mock serves it,
  or `tests/test_client_mock_drift.py` will fail.
- One model per module; export from `models/__init__.py` and
  `simpro_client/__init__.py`.

## 8. Endpoints (`endpoints/`)

- One class per resource, subclassing `ResourceEndpoint[Model]`, setting
  `model`, `collection_path`, `detail_path`, `item_key`.
- Path templates use `str.format` names. Collection paths end with `/`;
  detail paths do not. This matches the mock routes exactly.
- Nested scopes (`customer_id`, `site_id`, `job_id`) are passed as keyword
  arguments. `company_id` must be passed explicitly. The settings'
  `company_id_service` / `company_id_projects` are **not** applied
  automatically. Do not add implicit defaulting without a task.
- A new endpoint needs: the class, registration in `SimproClient.__init__`,
  exports in `endpoints/__init__.py`, an entry in
  `tests/test_route_contract.py`, and tests in `tests/test_endpoints.py`.

## 9. Pagination (`endpoints/base.py`)

- `fetch_page()` makes one request and returns `Page` (`items`, `page`,
  `page_size`, `total`, `count`, `pages`) from the `Result-Total`,
  `Result-Count` and `Result-Pages` headers.
- `iter_all()` is a lazy generator: no request until first iteration, one
  request per page, one page held in memory. It raises `SimproProtocolError`
  on a missing or invalid `Result-Pages` value, on a page past the last page,
  or on an empty page before the last page.
- Query parameters sent are `page` and `pageSize` (camelCase, as Simpro
  expects), plus caller `filters`. The client does not enforce the server's
  `pageSize` maximum of 250.

## 10. Rate limiting (`rate_limiter.py`)

- `TokenBucket(refill_rate, capacity, *, clock, sleeper)`. It is created once
  per `SimproClient` from `limiter_refill_rate` / `limiter_capacity`.
- `acquire()` is called for every attempt, including retries, and before
  every OAuth token request (`AuthManager` holds the same bucket).
- The lock covers only the token arithmetic. It must be released before
  sleeping. Keep `clock` and `sleeper` injectable for tests.
- Limitation: the budget is per client instance, not per process or per
  Simpro build. Real Simpro's limit (10 req/s) is per build. Do not add
  cross-process coordination without an ADR.

## 11. Dependencies

Runtime, pinned in root `pyproject.toml`: `httpx==0.28.1`,
`pydantic==2.13.4`, `pydantic-settings==2.14.2`, `python-dotenv==1.1.0`.
Do not add `requests`, `aiohttp`, retry libraries (e.g. `tenacity`), or
caching/ORM libraries. Upgrade pins only as a deliberate, stated change.

## 12. Code quality note

`client.py` is fully type-hinted and every function has a docstring.
`ruff check` passes on it; `ruff format --check` does not, because of four
pre-existing compressed call sites (the `SimproNotFoundError`,
`SimproClientError` and `SimproServerError` raises in `_request_response`,
and the `logging.LogRecord(...)` call in `_log_request`). Leave them unless a
task asks for them.

`rate_limiter.py` is typed but has no class or method docstrings. In
`endpoints/base.py` only `_route_values` and `_render` lack type hints; it has
no docstrings, and it has lines over 88 characters. When you modify a
function in these files, give it type hints and a docstring and keep it within
the line length. Do not reformat the whole file as a side effect.
