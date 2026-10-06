# CLAUDE.md — `tests/`

Complements the root `CLAUDE.md`. All tests here target `simpro_client`, or
the running mock over HTTP. Configuration lives in root `pyproject.toml`
(`testpaths = ["tests"]`, `pythonpath = ["src"]`, marker `integration`).

## 1. Test layers

| Layer | Where | Runs | Network |
|---|---|---|---|
| Offline unit | `tests/test_*.py` (default) | always | none: `respx` intercepts all `httpx` traffic |
| Mock integration | modules marked `pytest.mark.integration` (currently `test_simpro_mock_v2.py`) | only when `simpro-mock` is up on `localhost:8100` | real HTTP to the local mock only |
| Manual diagnostic | `scripts/verify-simpro-mock.py` | by hand | local mock |
| Live Simpro | **does not exist** | never | — |

Rules:
- New tests are offline unit tests unless the behaviour can only be proven
  against the running mock.
- Integration tests must carry `pytestmark = pytest.mark.integration` **and**
  skip at runtime (not at import) when `GET http://localhost:8100/health`
  fails. Follow `test_simpro_mock_v2.py`.
- No test may contact real Simpro (`*.simprosuite.com`) or any external host.
  Do not create a "live" marker or live-test layer. Real API access is not
  available, and adding it needs Alex's decision.
- Tests never connect to PostgreSQL directly and never import `simpro_mock`.
  The mock is exercised only through its HTTP API.

## 2. Commands

```bash
uv run pytest -q -m "not integration"          # required offline gate
uv run pytest -q                               # same, integration auto-skips
uv run pytest -m integration -v                # needs: docker compose up -d --build simpro-mock
uv run pytest tests/test_retries.py -v         # one module
uv run pytest -q --durations=5                 # spot slow tests
```

Baseline (re-verify before relying on this): the offline gate
(`-m "not integration"`) gives 56 passed, 2 deselected; plain `pytest -q`
gives 56 passed, 2 skipped (mock not running). Either takes about 17 s, about
15 s of which is one test (see §4).

## 3. Fixtures and settings

- Use `mock_settings` (client credentials) or `api_key_settings` from
  `conftest.py`, and construct clients as `SimproClient(settings=...)`.
- Never call `get_settings()` in tests and never depend on `.env`.
  `get_settings()` reads `.env` and is `lru_cache`d, so state leaks across
  tests.
- Build respx routes from `mock_settings.base_url` / `mock_settings.token_url`
  rather than retyping URLs. (`conftest.py` uses `/oauth/token`, not the real
  `/oauth2/token`; this is harmless because routes are built from the
  fixture, but do not copy the literal elsewhere.)
- Add shared fixtures to `conftest.py` only when two or more modules need
  them.
- Use `with SimproClient(...) as client:` so HTTP clients are closed.

## 4. Determinism and time

- Never let a test really sleep or depend on wall-clock time. Use the
  existing seams:
  - `TokenBucket(rate, capacity, clock=fake.clock, sleeper=fake.sleep)`; the
    fake sleeper must advance the fake clock, or the wait loop spins.
  - `client._sleep`, `client._random`, `client._now` on `SimproClient`, as in
    `tests/test_retries.py`.
- Any test whose mocked response is a 429 must replace `client._sleep`.
  `test_client.py::test_429_raises_rate_limit_error` does not, so it sleeps
  15 s for real (3 retries × `Retry-After: 5`). This is a known defect. Fix it
  only when asked.
- Tests that set a correlation ID must set it inside the test (for example
  `set_correlation_id("...")`), not at module level. The ID lives in a
  `ContextVar` shared across the run.
- Integration tests must not assert exact seeded values. The seed uses a
  fixed `random` seed, but its dates are relative to `date.today()`, and
  the seed values are not a contract. Assert shapes, headers, status codes,
  and stable invariants (companies `1` and `2` exist, PascalCase keys,
  `Result-*` headers, 401 without a token).

## 5. Structure and naming

- Test modules are `test_<subject>.py` and contain only `test_*` functions
  and fixtures.
- **No module-level side effects:** no network calls, no `respx.mock` blocks,
  no asserts, no `print`s at import time. Pytest imports every `test_*.py`
  during collection.
- Helpers must not be named `test_*`, or pytest collects them.
- Known exception: `tests/test_manual_logging.py` is a script (module-level
  code, no test functions; it sets a global correlation ID at import). Do not
  add more files like it; manual scripts belong in `scripts/`.
- Parametrize repeated cases (`@pytest.mark.parametrize`), as
  `test_endpoints.py` and `test_models.py` do.

## 6. What to test where

| Change | Update or add |
|---|---|
| Route template | `test_route_contract.py` (deliberate contract change) + `test_endpoints.py` |
| Model field or alias | `test_models.py` (alias, snake_case, optionality, `extra="ignore"`, date types) |
| Pagination | `test_pagination.py` (laziness, request count, `SimproProtocolError` cases) |
| Retry / error mapping | `test_retries.py`, `test_client.py` |
| Token bucket | `test_rate_limiter.py` (fake clock; lock released before sleep) |
| Auth | `test_auth.py` |
| Settings | `test_config.py` |
| Mock API behaviour | integration test (skip-gated), plus the client-side offline test |

Assert behaviour that callers depend on: request URL and params, headers,
the number of requests made, the exception type and its context
(`status_code`, `correlation_id`, `retry_after`). Do not just assert that
nothing raised.

## 7. Regression and quality rules

- Before reporting any change as done, run the full offline suite and report
  the real pass/skip/fail counts.
- Never delete, skip, `xfail` or weaken an assertion to make a failing test
  pass. Report the failure and its cause.
- Changing an expected value in `test_route_contract.py` or `test_models.py`
  is a contract change. Explain why in your report.
- Lint follows root `CLAUDE.md` §7: new test files must be clean, and
  modified files must not gain new violations.
- `tests/__pycache__/*.pyc` files are still tracked in git. After a run they
  show as modified. Restore them (`git checkout -- tests/__pycache__`) and
  never stage them.
