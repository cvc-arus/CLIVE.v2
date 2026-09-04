# Testing Guide — Phase 3

There are three distinct layers of testing in Phase 3, deliberately kept separate.

## 1. Unit Tests (`tests/*.py`, offline, always run)

| File | Tests | What it covers |
|---|---|---|
| `test_auth.py` | 5 | Token obtained on first call, cached on second, expiry triggers refresh, invalid credentials raise `SimproAuthError`, API-key mode returns the static token |
| `test_client.py` | 5 | Successful GET, 401 triggers refresh-and-retry, 404 raises `SimproNotFoundError`, 429 raises `SimproRateLimitError`, context-manager close behaviour |
| `test_config.py` | 3 | Settings load from explicit values, missing required field raises, defaults apply correctly |
| `test_logging.py` | 5 | Correlation ID set/get, auto-generation when unset, `JSONFormatter` includes correlation ID, `JSONFormatter` includes HTTP fields, `configure_logging()` returns a usable logger |

**Total: 18 tests, all passing, fully offline** (verified by running `pytest tests/ -v`, not just reading the files). All HTTP traffic is intercepted with `respx`; no network or live service is required.

```bash
pytest tests/ -v
```

`tests/conftest.py` supplies two fixtures: `mock_settings` (Client Credentials mode) and `api_key_settings` (API Key mode), both fully synthetic — no `.env` file needed to run the suite.

## 2. Manual/Interactive Script (not a pytest test)

`tests/test_manual_logging.py` is a script, not a test module — it has no `test_*` functions, only module-level code that prints structured JSON logs for visual inspection. `pytest` collects the file but finds zero test items in it (this is harmless, not a failure). Run it directly to eyeball log output:

```bash
python tests/test_manual_logging.py
```

## 3. Live Integration / Smoke Tests Against the Mock Service

Two files exercise the running `simpro-mock` container over real HTTP:

- **`tests/test_simpro_mock_v2.py`** — the current, correct version. It checks `GET http://localhost:8100/health` first; if the mock isn't reachable, every test in the file is skipped via `pytest.mark.skipif`, so `pytest tests/` never fails just because nobody started the mock. Covers: PascalCase field casing + pagination headers on `/companies/`, and a 401 on an unauthenticated request.
- **`tests/test_simpro_mock.py`** — the original script-style predecessor. It runs module-level `assert` statements at import time, unconditionally requiring `http://localhost:8100` to be up. **This file should be deleted** now that `test_simpro_mock_v2.py` supersedes it — see `docs/known-issues.md`. Until it's removed, be aware that a plain `pytest tests/` will fail this specific file if the mock isn't running (it does not skip).

```bash
docker compose up -d simpro-mock
pytest tests/test_simpro_mock_v2.py -v
```

## 4. Manual Diagnostic Script

`scripts/verify-simpro-mock.py` (521 lines) is a comprehensive manual diagnostic — not a pytest test, and deliberately kept outside `tests/` because its helper functions are named `test_list_endpoint`, `test_single_endpoint`, etc. If it lived inside `tests/`, pytest would try (and fail) to collect and run those helpers as real tests. It exercises every one of the mock's 12 resources plus auth and health, printing pass/fail diagnostics and exiting non-zero on any failure.

```bash
docker compose up -d simpro-mock
python scripts/verify-simpro-mock.py
```

## 5. Linting (part of the test/verification pipeline)

```bash
ruff check src/ --fix
ruff format src/
```

Zero-error linting is expected before any change is considered verified, per the project's development standards.

## 6. What "Sprint Complete" Means in This Project

A sprint (or a review pass) is not considered complete on the strength of a code read alone. The standing practice on this project is: **run the actual test suite**, because that's what previously surfaced real bugs (pytest-collection breakage from script-style test files, phantom `test_*`-named helpers) that a static read of the code would have missed.
