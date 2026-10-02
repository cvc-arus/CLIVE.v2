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
- Required: `base_url`, `token_url`, `client_id`, `client_secret`.
- Optional with defaults: `api_key`, `auth_mode`, `company_id_service` (1),
  `company_id_projects` (2), `timeout`, `max_retries` (3),
  `limiter_capacity` (8), `limiter_refill_rate` (8.0).
- Every new setting needs a type, a default only if a safe default exists, a
  `Field(description=...)`, and a matching entry in `.env.example`.
- `SimproClient(settings=...)` must keep accepting explicit settings, so
  callers and tests never need a `.env` file.

## 4. Authentication (`auth.py`, ADR-005)

- Default `auth_mode="client_credentials"`: form-encoded POST to `token_url`,
  token cached in memory, refreshed 60 s before `expires_in`.
- `auth_mode="api_key"`: static token from settings.
- `invalidate()` forces a refresh. The client uses it on a 401.
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
| `httpx.HTTPError` (network/timeout) | `SimproAPIError(status_code=0)`, no retry |
| 401 | invalidate token, retry once (separate budget), then error |
| 429 | retry up to `max_retries`; honour `Retry-After`, else backoff |
| 404 | `SimproNotFoundError` |
| other 4xx | `SimproClientError` |
| 5xx | `SimproServerError`, no retry |
| 204 | `None` from the raw methods |

Retry details: `Retry-After` is parsed as **integer seconds** or an HTTP-date.
If missing or unparseable, backoff is `min(60, 2**n * (0.5 + random()))`.
The same correlation ID is reused on every attempt of one logical request.
A 401 refresh followed by a 429 does not consume the 429 budget.

Known deviations from ADR-010 (report them; do not "fix" them without a task):
- Decimal `Retry-After` values (e.g. `2.5`) are treated as unparseable and
  fall back to backoff. ADR-010 says they should be honoured.
- Only 429 is retried. 5xx and network errors are not, although ADR-010's
  context mentions transient errors.
- The hierarchy keeps `SimproAPIError` between `SimproError` and
  `SimproClientError` / `SimproServerError`, for backward compatibility.

## 6. Exceptions (`exceptions.py`)

```
SimproError
├── SimproAuthError
├── SimproProtocolError          (bad or missing pagination headers)
└── SimproAPIError               (status_code, response_body, method, url,
    │                             correlation_id, retry_count)
    ├── SimproClientError        4xx
    │   ├── SimproNotFoundError  404
    │   └── SimproRateLimitError 429 (retry_after, attempt_count)
    └── SimproServerError        5xx
```

New exceptions subclass the closest existing class. Raised API errors must
carry `method`, `url` and `correlation_id`. Do not raise bare `Exception`,
`ValueError` or `httpx` errors across the public API for HTTP or protocol
failures. (Missing route parameters currently raise `ValueError` from
`ResourceEndpoint._render`; that is existing behaviour.)

## 7. Models (`models/`)

- Every resource model subclasses `SimproBaseModel` (`extra="ignore"`,
  `validate_by_alias=True`, `validate_by_name=True`).
- Every field has an explicit PascalCase `alias` and a snake_case attribute.
- Required vs optional must match the mock response schema
  (`services/simpro_mock/simpro_mock/schemas.py`) and
  `docs/phase3/phase3-sprint4-contract.md`. Where they disagree, report it.
- Dates are `datetime.date`; timestamps are `datetime.datetime`.
- Do not add fields the mock does not return unless they are optional and
  you can cite real Simpro documentation for them.
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
- `acquire()` is called for every attempt, including retries.
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

`client.py` lacks most type hints and docstrings. `rate_limiter.py` is typed
but has no class or method docstrings. In `endpoints/base.py` only
`_route_values` and `_render` lack type hints; it has no docstrings.
`client.py` and `endpoints/base.py` have lines over 88 characters. When
you modify a function in these files, give it type hints and a docstring and
keep it within the line length. Do not reformat the whole file as a side
effect.
