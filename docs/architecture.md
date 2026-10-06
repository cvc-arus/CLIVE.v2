# CLIVE Platform Architecture (Phases 1–3, As-Built)

Generated from the codebase in `git@github.com:cvc-arus/CLIVE-I.git` (branch `develop`) on 2026-09-04.

---

## 1. Overview

CLIVE is a self-hosted Enterprise AI Platform for CVC (CCTV and Security), deployed via Docker Compose on a single Ubuntu 24.04 development host. Phase list and phase status: `docs/roadmap.md`.

## 2. Container Topology

All services are defined in the single root `docker-compose.yml`:

| Service | Image / Build | Container name | Port mapping | Depends on |
|---|---|---|---|---|
| `ollama` | `ollama/ollama` | `clive-ollama` | `127.0.0.1:11435:11434` | — |
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | `clive-webui` | `127.0.0.1:3000:8080` | `postgres` (healthy), `tika`, `ollama` |
| `postgres` | `pgvector/pgvector:0.8.6-pg16` | `clive-postgres` | `127.0.0.1:5432:5432` | — |
| `tika` | `apache/tika:3.3.1.0-full` | `clive-tika` | `127.0.0.1:9998:9998` | — |
| `simpro-mock-db` | `postgres:16-alpine` | `clive-simpro-mock-db` | `127.0.0.1:5433:5432` | — |
| `simpro-mock` | built from `./services/simpro_mock` | `clive-simpro-mock` | `127.0.0.1:8100:8000` | `simpro-mock-db` (healthy) |

`ollama` requests one NVIDIA GPU device via the Compose `deploy.resources.reservations.devices` block, matching the RTX 3080 development hardware.

**Two separate Postgres instances by design:** `postgres` (Phase 2, PGVector-enabled, holds the RAG knowledge base) and `simpro-mock-db` (Phase 3, plain Postgres 16, holds the mock Simpro schema) are intentionally kept apart, on different ports (5432 vs 5433), so that Phase 3 development and testing can never touch production knowledge-base data.

Every published port binds to `127.0.0.1`, so no service is reachable from the LAN. To reach Open WebUI from another machine, use an SSH tunnel (for example `ssh -L 3000:localhost:3000 <host>`).

**Volumes:** `ollama`, `open-webui` and `postgres` use host bind mounts (`/data/ollama`, `/data/openwebui_data`, `/data/pgvector_data`). The only named volume is `simpro-mock-db-data`.

**Mock database credentials:** `simpro-mock-db` takes `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` from the `.env` keys `SIMPRO_MOCK_DB_USER`, `SIMPRO_MOCK_DB_PASSWORD` and `SIMPRO_MOCK_DB_NAME`, and `simpro-mock`'s `SIMPRO_MOCK_DATABASE_URL` is built from the same keys. `docker compose` refuses to start if any of them is unset.

**Healthchecks:** `postgres` and `simpro-mock-db` use `pg_isready`; `simpro-mock` calls its own `GET /health` with Python's `urllib` (the `python:3.12.3-slim-bookworm` image has no `curl`).

## 3. Phase 1 — Local AI Platform

- **Ollama**: local LLM inference engine, models pulled manually (`llama3.2`, `qwen2.5-coder:7b`).
- **Open WebUI**: chat interface, configured (in Phase 2) to use PGVector + Tika instead of its default embedded store.

## 4. Phase 2 — Production RAG

```
Open WebUI ──► Apache Tika (extraction) ──► Ollama (nomic-embed-text) ──► PostgreSQL + PGVector
```

- Postgres bound to `127.0.0.1` only (not `0.0.0.0`) to prevent external network exposure.
- Hybrid Search (BM25 + vector similarity + CrossEncoder reranking) enabled.
- Chunking tuned from defaults (1000/100) to 1500 characters / 200 overlap to preserve context around technical specifications, model numbers, and compliance clauses.
- Automated backup via `scripts/backup.sh` (dump → compress → integrity/restore verification → rotation).

## 5. Phase 3 — Simpro Integration

### 5.1 `simpro_client` (Python package, `src/simpro_client/`)

Library-first design: importable by any future phase without requiring a network service in between. Current modules:

| Module | Responsibility |
|---|---|
| `config.py` | `SimproSettings` (pydantic-settings), env prefix `SIMPRO_`, loads from `.env`, `extra="ignore"` so it coexists with unrelated Postgres/PGVector keys in the same `.env` file. `get_settings()` is `lru_cache`d. |
| `auth.py` | `AuthManager` — OAuth2 Client Credentials with in-memory token caching (60-second early-refresh buffer) and refresh, plus a static API Key fallback mode. |
| `client.py` | `SimproClient` — thin `httpx.Client` wrapper. `get/post/patch/delete` all funnel through `_request()`, which calls `_request_response()`: it waits on the rate limiter, attaches `Authorization: Bearer <token>` and `X-Correlation-ID` headers, times the call, logs it, and handles the status code (below). `_request()` then returns `None` for `204`, otherwise the parsed JSON body. |
| `exceptions.py` | Typed hierarchy: `SimproError` → `SimproAuthError`, `SimproProtocolError` (bad or missing pagination headers), `SimproAPIError(status_code, response_body)`; `SimproAPIError` → `SimproClientError` (4xx) and `SimproServerError` (5xx); `SimproClientError` → `SimproRateLimitError(retry_after)`, `SimproNotFoundError`. |
| `logging.py` | `ContextVar`-based correlation IDs (`get_correlation_id`/`set_correlation_id`), a `JSONFormatter` that emits single-line JSON logs to `stderr`, and a `RequestTimer` context manager for millisecond-precision timing. |

**Response handling in `client.py`:**
- `401` → invalidate cached token, retry exactly once (`_retry_on_401` flag prevents infinite loops)
- `429` → retry up to `max_retries` (`SIMPRO_MAX_RETRIES`), waiting for `Retry-After` if present, else exponential backoff; then `SimproRateLimitError`
- `404` → `SimproNotFoundError`
- any other `4xx` → `SimproClientError`
- `5xx` → `SimproServerError` (not retried)
- network error → `SimproAPIError` with `status_code` 0
- `204` → `None`
- otherwise → parsed JSON body

This is implemented with deviations from ADR-010; they are listed in `src/simpro_client/CLAUDE.md`.

Typed client layer: `models/` (one Pydantic model per resource, PascalCase-aliased), `endpoints/` (generic `ResourceEndpoint` in `base.py`, with `get()`, `fetch_page()` and `iter_all()` for pagination, plus one module per resource, exposed as attributes such as `client.jobs`), and `rate_limiter.py` (`TokenBucket`, configured by `SIMPRO_LIMITER_CAPACITY` / `SIMPRO_LIMITER_REFILL_RATE`). There is no separate `pagination.py`.

### 5.2 `simpro_mock` (FastAPI service, `services/simpro_mock/`)

A high-fidelity stand-in for the real Simpro REST API, built so that `simpro_client` needs zero code changes when real Simpro credentials arrive — only `SIMPRO_BASE_URL` / `SIMPRO_TOKEN_URL` change.

```
services/simpro_mock/
├── Dockerfile
├── alembic.ini, alembic/            # schema migrations
├── pyproject.toml
└── simpro_mock/
    ├── main.py          # FastAPI app, registers health/token/api routers + auth middleware
    ├── config.py         # Settings, env prefix SIMPRO_MOCK_
    ├── database.py       # SQLAlchemy engine/session/Base/get_db
    ├── middleware.py      # BearerAuthMiddleware, paginate_query, set_pagination_headers
    ├── filtering.py       # Simpro-style operator query filtering
    ├── models.py          # 12 SQLAlchemy 2.0 ORM models
    ├── schemas.py          # 12 Pydantic PascalCase response schemas
    ├── routers.py          # 26 routes (health, token, 24 GET routes for 12 resources)
    └── seed.py            # Seeds two companies + representative data
```

**Auth flow:** `POST /oauth2/token` accepts any form-encoded `client_id`/`client_secret` (development-only — no real credential check) and returns a static bearer token (`mock-access-token-simpro` by default) with a configurable `expires_in`. `BearerAuthMiddleware` then requires `Authorization: Bearer <that exact token>` on every route except `/health`, `/oauth2/token`, `/docs`, `/openapi.json`, `/redoc`.

**Pagination:** `paginate_query()` in `middleware.py` takes `page` (default 1) and `pageSize` (default 30, max 250), computes total/offset/total_pages, and `set_pagination_headers()` writes `Result-Total`, `Result-Count`, `Result-Pages` on the response — matching real Simpro's documented header contract.

**Filtering (`filtering.py`):** Query params are mapped from Simpro's PascalCase field names (`ID`, `Name`, `CompanyID`, `GivenName`, `FamilyName`, `Email`, `Phone`, `Status`, `DateIssued`, `Total`, `CustomerID`) to snake_case SQLAlchemy columns via `PASCAL_TO_SNAKE`, then parsed for operator syntax: `gt()`, `lt()`, `le()`, `ge()`, `ne()`, `between()`, `in()`, `!in()`, with a plain value falling back to exact match. `search=all` (default) combines filters with AND; `search=any` combines with OR.

### 5.3 Data model (12 resources)

```
Company (1) ──< Customer ──< Contact
             ──< Customer ──< Site ──< Asset
             ──< Customer ──< Project ──> Site
             ──< Job ──< JobNote ──> Employee
             ──< Job ──< Attachment
             ──< Quote ──> Customer
             ──< Employee
             ──< Status
```

All foreign keys cascade appropriately (`ondelete="CASCADE"` for strict ownership, `SET NULL` for optional links like `Quote.customer_id` and `Project.site_id`). Every relationship is declared with `back_populates` on both sides.

### 5.4 Endpoint surface (mock service, all read-only)

| Resource | List | Detail | Nested under |
|---|---|---|---|
| Companies | `GET /api/v1.0/companies/` | `GET /api/v1.0/companies/{company_id}` | — |
| Customers | `GET .../customers/` | `GET .../customers/{customer_id}` | Company |
| Jobs | `GET .../jobs/` | `GET .../jobs/{job_id}` | Company |
| Quotes | `GET .../quotes/` | `GET .../quotes/{quote_id}` | Company |
| Contacts | `GET .../customers/{customer_id}/contacts/` | `GET .../contacts/{contact_id}` | Company → Customer |
| Sites | `GET .../sites/` | `GET .../sites/{site_id}` | Company |
| Assets | `GET .../sites/{site_id}/assets/` | `GET .../assets/{asset_id}` | Company → Site |
| Employees | `GET .../employees/` | `GET .../employees/{employee_id}` | Company |
| Projects | `GET .../projects/` | `GET .../projects/{project_id}` | Company |
| Job Notes | `GET .../jobs/{job_id}/notes/` | `GET .../notes/{note_id}` | Company → Job |
| Attachments | `GET .../jobs/{job_id}/attachments/` | `GET .../attachments/{attachment_id}` | Company → Job |
| Statuses | `GET .../statuses/` | `GET .../statuses/{status_id}` | Company |

Plus infrastructure routes: `GET /health` and `POST /oauth2/token`. Full parameter and response detail is in `docs/simpro-mock-api-reference.md`.

Write operations (POST/PATCH/DELETE) are out of scope for both the mock and `simpro_client` in this phase, per the ADR and original PDD non-goals.

### 5.5 Two-company model

`seed.py` seeds exactly two companies matching CVC's real Simpro setup: **CVC Service** (`company_id=1`) and **CVC Projects** (`company_id=2`), each with representative Customers, Jobs, Quotes, Contacts, Sites, Assets, Employees, Projects, Job Notes, Attachments, and Statuses (8 customers per company, 8 jobs per company, etc.). `simpro_client`'s `SimproSettings.company_id_service` / `company_id_projects` (defaulting to 1/2) mirror this.

## 6. Planned but Not Yet Decided

The Phase 3 → Phase 4 handoff mechanism — whether Phase 4 imports `simpro_client` directly as a Python library, or talks to it through a thin FastAPI service wrapper — is recorded as ADR-009 (`docs/ADR/adr-009-phase3-phase4-handoff.md`, Proposed, open). The library-first architecture decision from the original PDD favors direct import, but this needs to be formally confirmed before Phase 4 scoping begins.
