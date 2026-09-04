# CLIVE Platform Architecture (Phases 1–3, As-Built)

Generated from the codebase in `git@github.com:cvc-arus/CLIVE-I.git` (branch `develop`) on 2026-09-04.

---

## 1. Overview

CLIVE is a self-hosted Enterprise AI Platform for CVC (CCTV and Security), deployed via Docker Compose on a single Ubuntu 24.04 development host. As of this document, three phases have shipped code:

| Phase | Name | State |
|---|---|---|
| 1 | Local AI Platform (Ollama + Open WebUI) | Complete |
| 2 | Production RAG (PGVector + Tika) | Complete |
| 3 | Simpro API Integration | Client foundation + mock service complete; typed client layer not started |

## 2. Container Topology

All services are defined in the single root `docker-compose.yml`:

| Service | Image / Build | Container name | Port mapping | Depends on |
|---|---|---|---|---|
| `ollama` | `ollama/ollama` | `clive-ollama` | `11435:11434` | — |
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | `clive-webui` | `3000:8080` | `postgres` (healthy), `tika`, `ollama` |
| `postgres` | `pgvector/pgvector:0.8.6-pg16` | `clive-postgres` | `127.0.0.1:5432:5432` | — |
| `tika` | `apache/tika:3.3.1.0-full` | `clive-tika` | `127.0.0.1:9998:9998` | — |
| `simpro-mock-db` | `postgres:16-alpine` | `clive-simpro-mock-db` | `5433:5432` | — |
| `simpro-mock` | built from `./services/simpro_mock` | `clive-simpro-mock` | `8100:8000` | `simpro-mock-db` (healthy) |

`ollama` requests one NVIDIA GPU device via the Compose `deploy.resources.reservations.devices` block, matching the RTX 3080 development hardware.

**Two separate Postgres instances by design:** `postgres` (Phase 2, PGVector-enabled, holds the RAG knowledge base) and `simpro-mock-db` (Phase 3, plain Postgres 16, holds the mock Simpro schema) are intentionally kept apart, on different ports (5432 vs 5433), so that Phase 3 development and testing can never touch production knowledge-base data.

**Observed inconsistency:** the Compose file declares named volumes `ollama_data`, `openwebui_data`, and `pgvector_data` at the bottom, but the corresponding services actually use host bind-mounts (`/data/ollama`, `/data/openwebui_data`, `/data/pgvector_data`) rather than those named volumes. Only `simpro-mock-db-data` is an actively used named volume. This doesn't break anything (the declared-but-unused volumes are simply idle) but is worth cleaning up for clarity.

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
| `client.py` | `SimproClient` — thin `httpx.Client` wrapper. `get/post/patch/delete` all funnel through `_request()`, which attaches `Authorization: Bearer <token>` and `X-Correlation-ID` headers, times the call, logs it, and hands the response to `_handle_response()`. |
| `exceptions.py` | Typed hierarchy: `SimproError` → `SimproAuthError`; `SimproAPIError(status_code, response_body)` → `SimproRateLimitError(retry_after)`, `SimproNotFoundError`. |
| `logging.py` | `ContextVar`-based correlation IDs (`get_correlation_id`/`set_correlation_id`), a `JSONFormatter` that emits single-line JSON logs to `stderr`, and a `RequestTimer` context manager for millisecond-precision timing. |

**Response handling in `client.py`:**
- `401` → invalidate cached token, retry exactly once (`_retry_on_401` flag prevents infinite loops)
- `404` → `SimproNotFoundError`
- `429` → `SimproRateLimitError`, reading `Retry-After` if present
- any other `>=400` → `SimproAPIError`
- `204` → `None`
- otherwise → parsed JSON body

Not yet present: `models/` (typed Pydantic resource models), `endpoints/` (resource-specific endpoint modules), `pagination.py`, `rate_limiter.py`. These were planned in the original PDD but have not been started in code.

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
    ├── routers.py          # 25 routes (health, token, 12 resources)
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

The Phase 3 → Phase 4 handoff mechanism — whether Phase 4 imports `simpro_client` directly as a Python library, or talks to it through a thin FastAPI service wrapper — has not been recorded as an ADR yet. The library-first architecture decision from the original PDD favors direct import, but this needs to be formally confirmed before Phase 4 scoping begins.
