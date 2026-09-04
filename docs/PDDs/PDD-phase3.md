# Phase 3 Project Design Document — Simpro API Integration (As-Built)

**Project:** CLIVE Enterprise AI Platform
**Company:** CVC (CCTV and Security)
**Repository:** `git@github.com:cvc-arus/CLIVE-I.git` (branch `develop`)
**Document status:** As-built, generated from the codebase on 2026-09-04
**Supersedes:** The original Phase 3 PDD drafted before live Simpro API access was known to be unavailable (see `Phase3-Sprint1.txt`)

---

## 1. Objective

Build a reusable, typed Python integration layer for the Simpro REST API that will serve as the shared data-access layer for Phase 4 (Document Generation) and later phases, without requiring live Simpro Premium API credentials during development.

## 2. Why the Original Plan Changed

The original PDD assumed live Simpro sandbox access and planned to build typed endpoint modules early (Sprint 2), tested against a thin mock. Once it was confirmed CVC has **no live Simpro API access**, the team made an architecture decision (`docs/ADR/adr-mock-simpro-api.md`) to build a **high-fidelity mock service first**, covering all 12 target resources with realistic pagination, filtering, and PascalCase field fidelity. This means only `SIMPRO_BASE_URL` (and `SIMPRO_TOKEN_URL`) need to change when live access arrives — no client code changes.

This is documented in full in `RevisedScope.txt`, which supersedes the original 6-sprint plan.

## 3. Current State of the Codebase (verified by running the test suite, not just reading it)

| Component | Status | Evidence |
|---|---|---|
| `src/simpro_client/` — config, auth, base HTTP client, exceptions, structured logging | ✅ Built and tested | 18/18 unit tests pass (`pytest tests/ -v`, respx-mocked, no live dependency) |
| `services/simpro_mock/` — FastAPI mock service + PostgreSQL schema + seed data | ✅ Built | 12 resources modelled, seeded, and routed; verified against a running instance |
| `simpro_client/models/` and `simpro_client/endpoints/` (typed Pydantic models + endpoint modules) | ❌ Not yet started | These directories do not exist in the current tree; only the foundation client (`client.py`, `auth.py`, `config.py`) is present |
| `pagination.py`, `rate_limiter.py` on the client side | ❌ Not yet started | Not present in `src/simpro_client/` |

**Important correction to the narrative in `RevisedScope.txt`:** that document describes a "Sprint 4 — Typed Client Layer" as "🔶 In Progress." The code shows no `models/` or `endpoints/` package under `simpro_client` yet — the typed layer has not been started in code. What *is* complete is the client foundation (Sprint 1) and the mock service (Sprint 3), plus a set of hardening fixes applied on top of them (see §6). Per the project's own principle — code is the source of truth — this document reflects the code, not the plan.

## 4. Architecture (as implemented)

```
                 CLIVE Platform
        ┌─────────────────────────────┐
        │   Open WebUI / future        │
        │   Phase 4+ services           │
        └───────────────┬──────────────┘
                         │ (planned: direct Python import)
        ┌────────────────▼──────────────┐
        │      simpro_client (Python)    │
        │  config → auth → client         │
        │        (no typed models/         │
        │         endpoints yet)           │
        └────────────────┬──────────────┘
                         │ HTTP (Bearer token)
        ┌────────────────▼──────────────┐
        │   simpro-mock (FastAPI, :8100) │
        │   ── BearerAuthMiddleware       │
        │   ── 12 resource routers        │
        │   ── pagination + filtering     │
        └────────────────┬──────────────┘
                         │ SQLAlchemy 2.0 (sync)
        ┌────────────────▼──────────────┐
        │  simpro-mock-db (Postgres 16,   │
        │  container port 5433)           │
        └─────────────────────────────────┘
```

When live Simpro access is enabled, `SIMPRO_BASE_URL` and `SIMPRO_TOKEN_URL` swap from the mock's URLs to `https://{build}.simprosuite.com/api/v1.0` and its token endpoint. No other change is required to `simpro_client`'s foundation layer.

## 5. Scope Delivered So Far

**In scope, delivered:**
- OAuth2 Client Credentials token management with in-memory caching, refresh, and 401-triggered retry (`simpro_client/auth.py`, `client.py`)
- API Key fallback auth mode
- Typed exception hierarchy (`SimproError` → `SimproAuthError`, `SimproAPIError` → `SimproRateLimitError`, `SimproNotFoundError`)
- Structured JSON logging with `ContextVar`-based correlation IDs, propagated as an `X-Correlation-ID` request header
- Configuration via `pydantic-settings`, `.env`-driven, `SIMPRO_` prefix, `extra="ignore"` so it coexists with PGVector's `.env` keys
- A full mock Simpro REST API (`simpro_mock`) covering 12 resources: Companies, Customers, Jobs, Quotes, Contacts, Sites, Assets, Employees, Projects, Job Notes, Attachments, Statuses
- Simpro-style query filtering (`gt()`, `lt()`, `le()`, `ge()`, `ne()`, `between()`, `in()`, `!in()`, `search=all|any`)
- Simpro-style pagination (`page`, `pageSize`, `Result-Total`/`Result-Count`/`Result-Pages` headers)
- PascalCase response field fidelity to match the real Simpro API shape
- Two-company seed data model (`CVC Service` = company 1, `CVC Projects` = company 2)
- Alembic migrations for the mock's schema
- Docker Compose integration (`simpro-mock`, `simpro-mock-db` services)

**In scope, not yet delivered:**
- Typed Pydantic resource models importable from `simpro_client.models`
- Endpoint modules (`simpro_client.endpoints.customers`, `.jobs`, etc.)
- Pagination iterator on the client side
- Token-bucket rate limiter on the client side (mock does not enforce/emit 429 either — see ADR limitations)
- Full retry/backoff policy beyond the single 401 retry
- Phase 3 → Phase 4 handoff ADR (direct import vs. service wrapper) — **not yet written**

**Not in scope (unchanged from original PDD):**
- Write operations (POST/PATCH/DELETE) against Simpro
- Caching/persistence layer beyond the mock's own database
- Real-time sync or webhooks
- UI/dashboard
- Authorization Code Grant (deferred to a future user-facing portal, Phase 6+)

## 6. Fixes Applied During Review

A codebase review (run against the actual test suite, not static reading) found and fixed:
1. A pytest-collection hazard: `tests/test_simpro_mock.py` was a script with module-level `assert` statements that ran at import time and required a live mock service, breaking collection whenever the mock wasn't running. A skip-gated version exists as `tests/test_simpro_mock_v2.py`. **Note:** the original `tests/test_simpro_mock.py` is still present in the tree alongside the new file — see `docs/known-issues.md`.
2. A phantom-test hazard: helper functions in a manual diagnostic script were named `test_*`, which pytest tried to collect and run. The script now lives at `scripts/verify-simpro-mock.py`, outside `tests/`, explicitly documented as "not a pytest test."
3. An unreachable branch in `client.py`'s correlation-ID handling was removed; the correlation ID is now generated once per request context and attached to the outgoing `X-Correlation-ID` header.
4. `simpro_mock/models.py` was normalized to consistent SQLAlchemy 2.0 style (`Mapped[]` / `mapped_column`, `back_populates` on both sides of every relationship).

`simpro_mock/schemas.py` — previously flagged as mixing `Optional[str]` and `str | None` — is now consistently `str | None` throughout; this item is resolved.

## 7. Risks Carried Forward

| Risk | Mitigation status |
|---|---|
| Real Simpro rate limits (10 req/sec/build) unknown in practice | Not yet mitigated — no client-side rate limiter exists yet |
| Real Simpro payload shape may differ from the mock's assumptions | Mock uses `from_attributes=True` Pydantic schemas per resource; real-world validation deferred until live access |
| No Phase 3 → Phase 4 handoff decision recorded | Open — ADR needed before Phase 4 scoping (see §8) |

## 8. Immediate Next Steps

1. Decide and record the **Phase 3 → Phase 4 handoff ADR** (direct `import simpro_client` vs. a thin FastAPI service wrapper).
2. Build `simpro_client/models/` (Pydantic models per resource, PascalCase-aliased) and `simpro_client/endpoints/` (endpoint modules over the existing base client).
3. Add a pagination iterator and token-bucket rate limiter to `simpro_client`.
4. Resolve the duplicate mock-integration test file (`test_simpro_mock.py` vs `test_simpro_mock_v2.py`).
5. Refresh `structure.txt`, which currently omits `scripts/verify-simpro-mock.py`, `services/simpro_mock/`, and `test_simpro_mock_v2.py`, and still lists `test_simpro_integration.py`, which no longer exists.
