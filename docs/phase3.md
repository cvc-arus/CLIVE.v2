# CLIVE-I: Phase 3 — Simpro API Integration

**Replaces** the previous `docs/phase3.md`, which documented only the `simpro_client` foundation (Sprint 1) and made no mention of the mock service. This version covers both halves of Phase 3 as they currently exist in the codebase.

---

## 📂 Directory Structure

```text
.
├── docker-compose.yml            # ollama, open-webui, postgres, tika, simpro-mock-db, simpro-mock
├── src/
│   ├── simpro_client/            # Reusable client library (Sprint 1 foundation)
│   │   ├── __init__.py
│   │   ├── auth.py               # OAuth2 token manager (caching + API key fallback)
│   │   ├── client.py             # Base HTTP client (auth injection, 401 retry, error handling)
│   │   ├── config.py             # SimproSettings via pydantic-settings
│   │   ├── exceptions.py         # Typed exception hierarchy
│   │   └── logging.py            # Correlation-ID JSON logger
│   └── simpro_client.egg-info/
├── services/
│   └── simpro_mock/              # Mock Simpro REST API (Sprint 3)
│       ├── Dockerfile
│       ├── alembic.ini, alembic/ # Schema migrations
│       ├── pyproject.toml
│       └── simpro_mock/
│           ├── main.py           # FastAPI app + middleware registration
│           ├── config.py         # Settings, env prefix SIMPRO_MOCK_
│           ├── database.py       # SQLAlchemy engine/session/Base
│           ├── middleware.py     # BearerAuthMiddleware, pagination helpers
│           ├── filtering.py      # Simpro-style operator query filtering
│           ├── models.py         # 12 SQLAlchemy 2.0 ORM models
│           ├── schemas.py        # 12 Pydantic PascalCase response schemas
│           ├── routers.py        # 25 routes (health, token, 12 resources)
│           └── seed.py           # Seeds CVC Service (id=1) + CVC Projects (id=2)
├── scripts/
│   └── verify-simpro-mock.py     # Manual diagnostic (not a pytest test — see docs/testing.md)
├── tests/
│   ├── conftest.py               # mock_settings / api_key_settings fixtures
│   ├── test_auth.py              # 5 tests
│   ├── test_client.py            # 5 tests
│   ├── test_config.py            # 3 tests
│   ├── test_logging.py           # 5 tests
│   ├── test_manual_logging.py    # Manual script (no test_* functions, not a real test)
│   ├── test_simpro_mock.py       # Legacy — module-level asserts, requires live mock (see known-issues.md)
│   └── test_simpro_mock_v2.py    # Current — skip-gated live smoke test
├── docs/
│   ├── phase1.md, phase2.md
│   ├── phase3-logging.md
│   └── ADR/adr-mock-simpro-api.md
└── pyproject.toml
```

---

## 🔌 Part A: `simpro_client` — Reusable Integration Client (Sprint 1)

See `docs/phase3-logging.md` for the logging subsystem in detail, and `docs/architecture.md` §5.1 for the module-by-module architecture. In summary:

- **Config**: `SimproSettings` loads from `.env`, prefix `SIMPRO_`, `extra="ignore"` so it coexists safely with unrelated Postgres/PGVector keys in the same file.
- **Auth**: `AuthManager` supports `client_credentials` (default) and `api_key` modes; OAuth tokens are cached in memory with a 60-second early-refresh buffer.
- **Client**: `SimproClient.get/post/patch/delete` route through a shared `_request()` that attaches the bearer token and an `X-Correlation-ID` header, times the call, logs it as structured JSON, retries once on `401`, and raises typed exceptions on `404`/`429`/other `4xx`/`5xx`.
- **Not yet built**: typed Pydantic models, endpoint modules, a pagination iterator, and a rate limiter. See `docs/PDD-phase3.md` §3 for the full gap analysis.

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest respx ruff pytest-cov   # dev deps (see docs/known-issues.md #5)
```

### Configuration

```env
SIMPRO_BASE_URL=http://simpro-mock:8000/api/v1.0
SIMPRO_TOKEN_URL=http://simpro-mock:8000/oauth2/token
SIMPRO_CLIENT_ID=your-client-id-here
SIMPRO_CLIENT_SECRET=your-client-secret-here
SIMPRO_AUTH_MODE=client_credentials
SIMPRO_COMPANY_ID_SERVICE=1
SIMPRO_COMPANY_ID_PROJECTS=2
```

### Run Tests (18 passing, offline)

```bash
pytest tests/ -v
ruff check src/ --fix
ruff format src/
```

---

## 🧱 Part B: `simpro_mock` — Mock Simpro REST API (Sprint 3)

A FastAPI + PostgreSQL service that mimics the real Simpro API closely enough that `simpro_client` requires zero code changes when live Simpro credentials arrive — only `SIMPRO_BASE_URL`/`SIMPRO_TOKEN_URL` change. Full rationale in `docs/ADR/adr-mock-simpro-api.md`; full endpoint reference in `docs/simpro-mock-api-reference.md`.

### Start It

```bash
docker compose up -d simpro-mock-db simpro-mock
curl http://localhost:8100/health
```

The container's `CMD` runs `alembic upgrade head`, then `python -m simpro_mock.seed`, then starts `uvicorn` — so by the time `/health` responds, the schema is migrated and seed data is loaded.

### What It Covers

- 12 resources: Companies, Customers, Jobs, Quotes, Contacts, Sites, Assets, Employees, Projects, Job Notes, Attachments, Statuses — all read-only (`GET`)
- Mock OAuth2 Client Credentials flow at `POST /oauth2/token` (accepts any credentials, issues a static bearer token)
- `BearerAuthMiddleware` enforcing that token on every route except `/health`, `/oauth2/token`, `/docs`, `/openapi.json`, `/redoc`
- Simpro-style pagination (`page`, `pageSize`, `Result-Total`/`Result-Count`/`Result-Pages` headers)
- Simpro-style filtering with operators (`gt`, `lt`, `le`, `ge`, `ne`, `between`, `in`, `!in`) and `search=all|any` combination
- PascalCase field fidelity in every JSON response
- Two-company seed data: `CVC Service` (id 1), `CVC Projects` (id 2)

### What It Deliberately Does Not Cover (see ADR)

- Real credential validation on `/oauth2/token`
- Rate limiting / `429` responses
- Webhooks or async event callbacks
- Write operations or business-logic state transitions

### Verify It

```bash
python scripts/verify-simpro-mock.py       # comprehensive manual diagnostic
pytest tests/test_simpro_mock_v2.py -v     # skip-gated pytest smoke test
```

---

## 📊 Observability (shared by both halves)

### Correlation IDs

```python
from simpro_client.logging import set_correlation_id
set_correlation_id("invoice-sync-01")
```

Every outgoing request from `SimproClient` carries this ID on the `X-Correlation-ID` header, and it appears in every structured log line for that operation.

### JSON Logs

```json
{"timestamp": "2026-08-18 14:43:08,211", "level": "INFO", "logger": "simpro_client", "message": "GET /companies/1/jobs/ -> 200 (45.2ms)", "correlation_id": "invoice-sync-01", "method": "GET", "url": "/companies/1/jobs/", "status_code": 200, "duration_ms": 45.2}
```

---

## Current Status Summary

| Item | Status |
|---|---|
| `simpro_client` foundation (config, auth, client, exceptions, logging) | ✅ Built, 18/18 tests passing |
| `simpro_mock` service (12 resources, auth, pagination, filtering, seed) | ✅ Built, verified against a running instance |
| `simpro_client` typed models + endpoint modules | ❌ Not started |
| `simpro_client` pagination iterator + rate limiter | ❌ Not started |
| Phase 3 → Phase 4 handoff ADR | ❌ Not written |

See `docs/PDD-phase3.md` for the full as-built design document, `docs/known-issues.md` for discrepancies found during this review, and `docs/roadmap.md` for what's next.
