# Phase 3 Project Design Document — Simpro API Integration (As-Built, Closed)

**Project:** CLIVE Enterprise AI Platform
**Company:** CVC (CCTV and Security)
**Repository:** `git@github.com:cvc-arus/CLIVE-I.git` (branch `develop`)
**Document status:** **Closed.** Phase 3 was closed by Alex on 2026-10-09. This
as-built revision was written on 2026-10-15 from the codebase at commit
`864264b` and is not maintained after that. Current architecture is in
`docs/architecture.md`; current status is in `docs/STATUS.md`.
**Supersedes:** the as-built version of 2026-09-04 (in git history), which
predated the typed client layer, and the original Phase 3 PDD drafted before
it was known that there was no live Simpro API access.
**Sign-off evidence:** `docs/phase3/phase3-signoff.md` (test run, close,
items carried past the close).

---

## 1. Objective

Build a reusable, typed Python integration layer for the Simpro REST API to
serve as the shared data-access layer for Phase 4 (Document Generation) and
later phases, without live Simpro API credentials during development.

## 2. Why the Original Plan Changed

The original plan assumed live Simpro sandbox access and built typed endpoint
modules early against a thin mock. Once it was confirmed that CVC had **no
live Simpro API access**, the mock service was built first
(`docs/ADR/adr-mock-simpro-api.md`), so that only configuration
(`SIMPRO_BASE_URL`, `SIMPRO_TOKEN_URL`, credentials) changes when live access
arrives. The revised plan is in `docs/scope/scope-rev2.md` (historical).

That cutover claim was first only asserted. In October 2026 Simpro's published
OpenAPI spec showed the mock's payloads did not match it (`docs/known-issues.md`,
entry RESOLVED 2026-10-08). ADR-013 re-shaped the mock and the client to that
contract, vendored at `docs/contracts/simpro-openapi-v1-get-subset.json`, so the
claim is now measured by `tests/test_spec_conformance.py` rather than asserted.

## 3. Delivered (as built)

Detail is owned by `docs/architecture.md` §5 and the directory `CLAUDE.md`
files; this section summarises it with file paths.

### 3.1 `simpro_client` (`src/simpro_client/`)

| Area | Files | Decision |
|---|---|---|
| Configuration via pydantic-settings, `SIMPRO_` prefix, per-`auth_mode` validation | `config.py` | ADR-007 |
| OAuth2 Client Credentials with in-memory token cache and early refresh; static API key fallback; refresh lock and token-aware invalidate | `auth.py` | ADR-005, ADR-012 |
| Sync `httpx.Client` transport: bearer and correlation-ID headers, one 401 retry, 429 and transient-error retries with a capped `Retry-After` | `client.py` | ADR-004, ADR-010, ADR-012 |
| Typed exception hierarchy with auth-error context | `exceptions.py` | ADR-011 |
| Token-bucket rate limiter, budget per client instance (default 8 req/s) | `rate_limiter.py` | ADR-010 |
| Structured JSON logging with `ContextVar` correlation IDs | `logging.py` | — |
| Typed Pydantic models, PascalCase-aliased, shaped to the vendored contract; money as `Decimal` | `models/` | ADR-013 |
| Generic `ResourceEndpoint` with `get()`, `fetch_page()`, `iter_all()` and `columns=`; one module per resource | `endpoints/` | ADR-006, ADR-013 |

ADR-010 is implemented with deviations, listed in `src/simpro_client/CLAUDE.md`.
There is no separate `pagination.py`; pagination lives in `endpoints/base.py`.

### 3.2 `simpro_mock` (`services/simpro_mock/`)

FastAPI + sync SQLAlchemy 2.0 + PostgreSQL 16 (`simpro-mock-db`, port 5433),
Alembic migrations, two-company seed data, and Docker Compose services
`simpro-mock` (port 8100) and `simpro-mock-db`, both bound to `127.0.0.1`.
GET-only resource routes shaped to the vendored contract, plus `/health` and a
development-only `POST /oauth2/token`. It honours `columns` on every route,
`orderby` and `limit` on collection routes, Simpro-style filter operators and
pagination headers, and returns `400` on an unknown filter or an unorderable
`orderby` field (`routers.py`, `serializers.py`, `projection.py`,
`filtering.py`, `ordering.py`, `middleware.py`).

Simpro has no Projects resource: a project is a Job with `Type="Project"`, so
the mock's earlier `projects` table and route were removed (ADR-013).

### 3.3 Tests (`tests/`)

Offline: `test_client.py`, `test_auth.py`, `test_config.py`, `test_logging.py`,
`test_models.py`, `test_endpoints.py`, `test_pagination.py`,
`test_rate_limiter.py`, `test_retries.py`, `test_route_contract.py` and
`test_spec_conformance.py` (with `spec_conformance_baseline.json`, which is
empty). Integration, needing the mock: `test_simpro_mock_v2.py` and
`test_client_mock_drift.py`. Layers and commands: `docs/testing.md` and
`tests/CLAUDE.md`. Test counts at the close: `docs/phase3/phase3-signoff.md`.

## 4. Architecture at the Close

```
        ┌──────────────────────────────────────┐
        │ clive-gateway (ADR-009, Phase 3B)     │
        │ planned; the only runtime importer    │
        └──────────────────┬───────────────────┘
                           │ Python import
        ┌──────────────────▼───────────────────┐
        │ simpro_client (src/simpro_client/)    │
        │ config · auth · client · rate limiter │
        │ models/ · endpoints/                  │
        └──────────────────┬───────────────────┘
                           │ HTTP (OAuth2 bearer token)
        ┌──────────────────▼───────────────────┐
        │ simpro-mock (FastAPI, :8100)          │
        │ later: {build}.simprosuite.com        │
        └──────────────────┬───────────────────┘
                           │ SQLAlchemy 2.0 (sync)
        ┌──────────────────▼───────────────────┐
        │ simpro-mock-db (Postgres 16, :5433)   │
        └──────────────────────────────────────┘
```

**Handoff (ADR-009, accepted):** a single `clive-gateway` service imports
`simpro_client` and serves every other consumer, Phase 4 included, over HTTP.
It does not exist yet; it is planned in Phase 3B
(`docs/PDDs/PDD-phase3b-simpro-conversational-access.md`). ADR-006's
library-first design stands; only its "no service wrapper" part is superseded.

## 5. Plan vs Delivery

| Planned (`scope-rev2.md`) | Outcome |
|---|---|
| Sprint 1 — client foundation | Delivered |
| Sprint 2 — architecture pivot | Delivered as planning (mock-first decision) |
| Sprint 3 — Simpro mock service | Delivered |
| Sprint 4 — typed client layer | Delivered (sprint records in `docs/phase3/sprints/`) |
| Sprint 5 — hardening and documentation | Delivered as the resilience ADRs (ADR-010 to ADR-012), the ADR-013 re-shape (seven sprints, 2026-10-07 to 2026-10-08) and the October documentation audit (`docs/doc-audit.md`) |
| Sprint 6 — Phase 4 readiness review | Replaced by the Phase 3B handover checklist (Phase 3B PDD §5) |

Not in scope, and not built: write operations, caching or persistence beyond
the mock's database, webhooks, a UI, and the Authorization Code Grant (ADR-005).

## 6. Decisions

ADR-004 (httpx), ADR-005 (auth), ADR-006 (library-first, partially superseded
by ADR-009), ADR-007 (configuration), ADR-009 (handoff), ADR-010 (resilience),
ADR-011 (exceptions), ADR-012 (retry ceiling and refresh concurrency), ADR-013
(published contract) and `adr-mock-simpro-api.md` (mock-first; its "Capabilities
& Coverage" superseded by ADR-013). ADR-008 was withdrawn as a duplicate of
ADR-010. Status of each: `docs/ADR/ADR-index.md`.

## 7. Carried Forward

| Item | Where it is tracked |
|---|---|
| No live Simpro API access at the close | `docs/STATUS.md` (Simpro access), course correction W1 |
| Four mock behaviours unverifiable without live credentials: `ID` in an unrequested `columns` projection, the `Result-*` pagination headers, `limit`'s semantics, `/companies/` pagination | `docs/phase3/phase3-signoff.md`, `docs/roadmap.md` |
| Real Simpro rate limits and token lifetime undocumented; conservative defaults kept | `docs/STATUS.md` (open risks), ADR-010, ADR-012 |
| The rate limiter's budget is per client instance, not per Simpro build | `src/simpro_client/CLAUDE.md` §10; the gateway runs a single worker (Phase 3B PDD §11) |
| `pip install -e ".[dev]"` does not install dev tools; use `uv sync` | `docs/known-issues.md` |

## 8. Close

Phase 3 was closed by Alex on 2026-10-09, once ADR-009 was decided. Evidence:
`docs/phase3/phase3-signoff.md`. Next: Phase 3B and Phase 4, in the order set
at the end of the course correction sprint (`docs/STATUS.md`).
