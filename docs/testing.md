# Testing Guide — Phase 3

There are three distinct layers of testing in Phase 3, deliberately kept separate.

## 1. Unit Tests (`tests/*.py`, offline, always run)

| File | What it covers |
|---|---|
| `test_auth.py` | Token obtained on first call, cached on second, expiry triggers refresh, invalid credentials raise `SimproAuthError` with the token endpoint's status (`None` on a transport error), API-key mode returns the static token, token requests acquire from the rate limiter (API-key mode does not) |
| `test_client.py` | Successful GET, 401 triggers refresh-and-retry, 404 raises `SimproNotFoundError`, 429 raises `SimproRateLimitError`, context-manager close behaviour |
| `test_config.py` | Settings load from explicit values, missing required field raises, defaults apply correctly, unknown `auth_mode` values are rejected, each `auth_mode` requires its own credentials (an empty value counts as missing) |
| `test_logging.py` | Correlation ID set/get, auto-generation when unset, `JSONFormatter` includes correlation ID, `JSONFormatter` includes HTTP fields, `configure_logging()` returns a usable logger |
| `test_models.py` | Typed resource models accept PascalCase aliases, ignore unknown fields, convert date/datetime fields, and parse money into `Decimal` from both a JSON number and a string |
| `test_endpoints.py` | Typed endpoints use the exact route and model, keep pagination headers and filters, reject a missing nested scope before any request, send `columns` as csv on both collection and detail routes, reject a `page_size` outside 1–250, and refuse `get()` on the list-only polymorphic customers endpoint |
| `test_pagination.py` | `iter_all()` is lazy, walks multiple pages, and raises `SimproProtocolError` on bad pagination metadata |
| `test_rate_limiter.py` | `TokenBucket` burst, refill and wait; lock released before sleeping |
| `test_retries.py` | `Retry-After` forms and backoff fallback, independent 401 and 429 budgets, one limiter shared by client and auth, retry exhaustion and typed errors, GET-only retry of 502/503/504 and timeouts/network errors, one budget shared with 429, failed refresh after a 401 raises `SimproAuthRefreshError`, a failed first token fetch raises `SimproAuthError` carrying the request context, a second 401 after refresh raises `SimproClientError` |
| `test_route_contract.py` | The read-only route inventory matches the committed contract; `item_key` names a placeholder its `detail_path` actually has; `EXPECTED_ROUTES` covers every exported endpoint class; and an endpoint with no detail route upstream must override `get()` |
| `test_spec_conformance.py` | Every client model validates payloads generated from the vendored contract `docs/contracts/simpro-openapi-v1-get-subset.json`, in both a `full` shape (every documented property) and a `minimal` shape (required properties only, nullables set to `null`). Known-nonconforming combinations are listed in `tests/spec_conformance_baseline.json` and enforced in both directions: a combination outside the file must conform, and one inside it that starts conforming fails until its entry is deleted (ADR-013). **That file is now empty and every check passes**, so `MAX_BASELINE_ENTRIES` is 0 and adding an entry is a regression rather than a way to land a change |

All tests except those marked `integration` run fully offline. All HTTP traffic is intercepted with `respx`; no network or live service is required. Run the offline suite with:

```bash
uv run pytest -q -m "not integration"
```

`tests/conftest.py` supplies two fixtures: `mock_settings` (Client Credentials mode) and `api_key_settings` (API Key mode), both fully synthetic — no `.env` file needed to run the suite.

## 2. Manual/Interactive Script (not a pytest test)

`tests/test_manual_logging.py` is a script, not a test module — it has no `test_*` functions, only module-level code that prints structured JSON logs for visual inspection. `pytest` collects the file but finds zero test items in it (this is harmless, not a failure). Run it directly to eyeball log output:

```bash
python tests/test_manual_logging.py
```

## 3. Live Integration / Smoke Tests Against the Mock Service

Two files exercise the running `simpro-mock` container over real HTTP. Both are marked `integration` (`pytestmark`) and both use an autouse fixture that checks `GET http://localhost:8100/health` and calls `pytest.skip()` at runtime if the mock isn't reachable — so a full `pytest` run never fails just because nobody started the mock.

- **`tests/test_simpro_mock_v2.py`** — drives the mock with raw `httpx`. Covers: PascalCase field casing and pagination headers on `/companies/`; a 401 on an unauthenticated request; the polymorphic customer routes being type-scoped and their `_href` resolving; a project being a job with `Type="Project"` and `/projects/` returning 404; `Job.Total` arriving as a nested object of two-decimal numbers; and the S6 query handling — `columns` narrowing a collection without losing the pagination headers, selecting whole nested blocks on a detail route, an empty `?columns=` behaving as if omitted, an unknown filter returning 400 with the usable field names, a known filter actually narrowing the result, and the six request-control parameters not being mistaken for filters.
- **`tests/test_client_mock_drift.py`** — drives the real `SimproClient` against the mock, which nothing did before (the file above never imports the client, and every client-side test uses `respx` and never touches the mock, so the two packages could drift apart with a green suite). Parametrized over every endpoint registered on `SimproClient`: the collection route resolves and parses into the declared model, the detail route resolves for an id taken from that list, and `iter_all()` walks every page. One further test asserts its endpoint table matches what `SimproClient` actually registers, so a renamed endpoint cannot escape the module. Scope ids are discovered from the mock at runtime, never hardcoded, and no exact seeded value is asserted (`tests/CLAUDE.md` §4). Two further tests cover `columns` end to end: a projection survives the client's validation, and projecting away a field the model marks required raises — which is real Simpro's behaviour too, not a mock quirk.

```bash
docker compose up -d --build simpro-mock
uv run pytest -m integration -v
```

## 4. Manual Diagnostic Script

`scripts/verify-simpro-mock.py` is a comprehensive manual diagnostic — not a pytest test, and deliberately kept outside `tests/` because its helper functions are named `test_list_endpoint`, `test_single_endpoint`, etc. If it lived inside `tests/`, pytest would try (and fail) to collect and run those helpers as real tests. It exercises every one of the mock's 25 routes plus auth and health, printing pass/fail diagnostics and exiting non-zero on the first failure — so expect to fix problems one at a time.

```bash
docker compose up -d --build simpro-mock
uv run python scripts/verify-simpro-mock.py
```

## 5. Linting (part of the test/verification pipeline)

Run on the paths you changed:

```bash
uv run ruff check <paths>
uv run ruff format --check <paths>
```

New files must pass both checks, and modified files must not gain new violations (root `CLAUDE.md` §7). The repository has existing lint debt, tracked in `docs/known-issues.md`, so `uv run ruff check .` does not pass yet. Do not run `ruff --fix` or `ruff format` on files outside your change.

## 6. What "Sprint Complete" Means in This Project

A sprint (or a review pass) is not considered complete on the strength of a code read alone. The standing practice on this project is: **run the actual test suite**, because that's what previously surfaced real bugs (pytest-collection breakage from script-style test files, phantom `test_*`-named helpers) that a static read of the code would have missed.
