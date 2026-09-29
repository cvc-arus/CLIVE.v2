# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

CLIVE is a self-hosted Enterprise AI Platform for CVC (a CCTV/security company), deployed via Docker Compose on a single Ubuntu host. Phases 1–2 (local LLM inference via Ollama/Open WebUI, RAG via PGVector + Tika) are complete infrastructure and rarely touched. Active development is Phase 3: a typed Python client (`simpro_client`) for the Simpro REST API, developed against a FastAPI mock service (`simpro_mock`) that stands in for real Simpro until production credentials arrive.

Two independent Python projects live in this repo, each with its own `pyproject.toml` and dependency lock:
- **`src/simpro_client/`** — the library. Root `pyproject.toml`, root `.venv`, `uv` managed.
- **`services/simpro_mock/`** — the FastAPI mock API. Its own `pyproject.toml`/`uv.lock`/`.venv` under `services/simpro_mock/`.

Documentation is treated as generated from code, not the other way around: `docs/development-standards.md` §9 states "Code is the sole source of truth" — when a planning doc (`docs/roadmap.md`, `docs/scope/`) and the code disagree, the code wins, and note the discrepancy rather than silently reconciling the doc. Never assume a component exists because it is described in a roadmap, scope document, ADR, or previous sprint summary. Verify its path and implementation in the repository before treating it as implemented.

## Commands

### simpro_client (root package)

```bash
# Tests — offline, no live dependency (respx mocks all httpx traffic)
pytest tests/ -v

# Single test file / test
pytest tests/test_client.py -v
pytest tests/test_client.py::test_name -v

# Lint & format
ruff check src/ --fix
ruff format src/

# Manual log-output inspection (not a pytest test, has no test_* functions)
python tests/test_manual_logging.py
```

`uv` is the package manager. **Argument order matters**: `ENV_VAR="..." uv run <cmd>` works; `uv run ENV_VAR="..." <cmd>` fails because `uv` tries to exec the env-var string as a binary. `pip install -e ".[dev]"` silently skips dev deps because they're declared under PEP 735 `[dependency-groups]`, not `[project.optional-dependencies]` — use `uv sync` instead.

### Integration testing against the mock service

```bash
docker compose up -d simpro-mock          # start the mock (rebuilds needed after source edits, see below)
pytest tests/test_simpro_mock_v2.py -v    # skip-gated: auto-skips if mock unreachable at :8100
python scripts/verify-simpro-mock.py      # manual diagnostic, exercises every resource, exits non-zero on failure
```

`scripts/verify-simpro-mock.py` deliberately lives outside `tests/` — its helper functions are named `test_list_endpoint` etc., which pytest would otherwise try to collect and run as real tests.

### simpro_mock service

The mock's `Dockerfile` bakes `simpro_mock/` source into the image at build time. **Editing source files on disk is not enough** — after any change, rebuild:

```bash
docker compose up -d --build simpro-mock
# or
docker compose build simpro-mock
```

Migrations run automatically on container start (`alembic upgrade head`) before seeding and `uvicorn` launch. To make a schema change: write an Alembic migration (`alembic revision` → edit → `alembic upgrade head`), never a manual `CREATE TABLE`.

### Full stack

```bash
docker compose up -d          # all services: ollama, open-webui, postgres, tika, simpro-mock-db, simpro-mock
```

## Architecture

### `simpro_client` layers

```
SimproClient (client.py)
  ├─ AuthManager (auth.py)       — OAuth2 Client Credentials w/ token cache, or static API key
  ├─ TokenBucket (rate_limiter.py) — client-side throttle, acquired before every request
  ├─ endpoints/*.py               — one class per resource (CompaniesEndpoint, JobsEndpoint, ...)
  │    └─ ResourceEndpoint (endpoints/base.py) — shared get / fetch_page / iter_all logic
  └─ models/*.py                  — one Pydantic model per resource, extends SimproBaseModel
```

- **`client.py`**: `SimproClient._request_response()` is the single funnel for every HTTP call. It attaches `Authorization` + `X-Correlation-ID` headers, acquires a rate-limit token, times the call, and handles the response: `401` → invalidate cached token and retry once; `429` → parse `Retry-After` (integer-seconds or HTTP-date) or fall back to exponential backoff with jitter, retrying up to `SIMPRO_MAX_RETRIES` times before raising `SimproRateLimitError`; `404` → `SimproNotFoundError`; other `4xx` → `SimproClientError`; `5xx` → `SimproServerError`; `204` → `None`.
- **`endpoints/base.py`**: `ResourceEndpoint` is generic over the Pydantic model and provides three read operations for every resource — `get(item_id, ...)`, `fetch_page(...)` (one page, returns a `Page` dataclass with `total`/`count`/`pages` from the `Result-*` response headers), and `iter_all(...)` (generator that walks every page, raising `SimproProtocolError` if the server's pagination headers are internally inconsistent — e.g. an empty page before the last one). Route templates (`collection_path`, `detail_path`) are `str.format()` templates filled from `company_id` plus arbitrary `**scope_ids` (e.g. `site_id` for nested Assets).
- **`models/base.py`**: `SimproBaseModel` sets `validate_by_alias=True, validate_by_name=True, extra="ignore"` so every resource model accepts the API's committed PascalCase field names *and* snake_case, ignoring unknown fields. Each resource model in `models/*.py` declares explicit aliases for its PascalCase payload fields and converts date/datetime strings to Python values.
- **`exceptions.py`**: `SimproError` → `SimproAuthError` / `SimproAPIError` → `SimproClientError` (`SimproRateLimitError`, `SimproNotFoundError`) / `SimproServerError`; `SimproProtocolError` for contract violations (bad/missing pagination headers) that aren't HTTP errors.
- **`config.py`**: `SimproSettings` (pydantic-settings), env prefix `SIMPRO_`, `extra="ignore"` so Simpro keys coexist in the same root `.env` as unrelated Postgres/PGVector keys. `get_settings()` is `lru_cache`d.
- **`logging.py`**: `ContextVar`-based correlation IDs threaded through every request/log line, `JSONFormatter` emitting single-line JSON to stderr.

### `simpro_mock` (FastAPI, `services/simpro_mock/simpro_mock/`)

Exists so `simpro_client` needs zero code changes when real Simpro credentials arrive — only `SIMPRO_BASE_URL`/`SIMPRO_TOKEN_URL` change. Synchronous SQLAlchemy 2.0 throughout (`Mapped[]`, `sessionmaker`, `psycopg2-binary`) — this is a deliberate standing decision; don't introduce `asyncpg`/async sessions without a dedicated ADR.

- `main.py` — FastAPI app wiring health/token/resource routers + `BearerAuthMiddleware`.
- `middleware.py` — `BearerAuthMiddleware` (every route except `/health`, `/oauth2/token`, `/docs`, `/openapi.json`, `/redoc` requires the exact static bearer token); `paginate_query()` / `set_pagination_headers()` implement the `page`/`pageSize` → `Result-Total`/`Result-Count`/`Result-Pages` header contract that `simpro_client`'s `fetch_page`/`iter_all` depend on.
- `filtering.py` — maps Simpro-style PascalCase query params to snake_case SQLAlchemy columns, supports operator syntax (`gt()`, `lt()`, `le()`, `ge()`, `ne()`, `between()`, `in()`, `!in()`) and `search=all|any` (AND/OR) combination.
- `models.py` / `schemas.py` — 12 SQLAlchemy ORM models and matching PascalCase Pydantic response schemas: `Company (1) ──< Customer ──< {Contact, Site ──< Asset, Project}`, `Job ──< {JobNote, Attachment}`, plus `Quote`, `Employee`, `Status`. FKs use `ondelete="CASCADE"` for strict ownership, `SET NULL` for optional links (e.g. `Quote.customer_id`); every relationship declares `back_populates` on both sides.
- `seed.py` — seeds exactly two companies mirroring CVC's real Simpro setup (`company_id=1` "CVC Service", `company_id=2` "CVC Projects"); `simpro_client`'s `SIMPRO_COMPANY_ID_SERVICE`/`SIMPRO_COMPANY_ID_PROJECTS` settings mirror these.
- All routes are currently **read-only** — write operations (POST/PATCH/DELETE) are out of scope for this phase per ADR and PDD.

### Two separate Postgres instances by design

`postgres` (Phase 2, PGVector-enabled, holds the RAG knowledge base, port 5432) and `simpro-mock-db` (Phase 3, plain Postgres 16, port 5433) are intentionally isolated so Phase 3 development/testing can never touch production knowledge-base data.

## Testing conventions

Three deliberately separate layers (see `docs/testing.md`):
1. **Unit tests** (`tests/test_auth.py`, `test_client.py`, `test_config.py`, `test_logging.py`, `test_models.py`, `test_endpoints.py`, `test_route_contract.py`, `test_pagination.py`, `test_rate_limiter.py`, `test_retries.py`) — fully offline, `respx` intercepts all `httpx` traffic. This is what `pytest tests/ -v` should run cleanly at all times.
2. **Manual script** (`tests/test_manual_logging.py`) — no `test_*` functions, pytest collects it but runs zero tests; run directly for visual log inspection.
3. **Live/skip-gated integration** (`tests/test_simpro_mock_v2.py`) — checks `GET http://localhost:8100/health` first and skips entirely if the mock isn't running, so `pytest tests/` never fails just because the container is down.

A sprint or review is not considered complete on a code read alone — run `pytest tests/ -v` (this project has previously caught pytest-collection bugs, like script-style test files with module-level asserts, that a static read missed).

## ADR context worth knowing before touching resilience/auth/config code

- **ADR-004**: httpx chosen as the HTTP client.
- **ADR-005**: Client Credentials is the primary auth mode; static API key is a fallback.
- **ADR-006**: `simpro_client` is library-first — importable directly by future phases, not accessed only through a network service.
- **ADR-007**: `pydantic-settings` is the configuration mechanism; no hardcoded secrets.
- **ADR-010**: client-side resilience (token-bucket rate limiting + retry/backoff on 429, typed error hierarchy) — approved and implemented in `client.py`/`rate_limiter.py`.
- **ADR-009** (open): whether Phase 4 imports `simpro_client` directly or talks to it through a service wrapper is an unresolved decision requiring sign-off — don't assume either direction when working on Phase 4-adjacent code.
