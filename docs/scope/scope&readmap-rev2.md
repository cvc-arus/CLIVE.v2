# CLIVE Enterprise AI Platform — Scope & Roadmap (Revision 2)

**Company:** CVC · **Industry:** CCTV and Security
**Supersedes:** original `Clive_Scope.txt` and the 6-sprint Phase 3 plan drafted before live Simpro access was known to be unavailable.
**Reason for revision:** Phase 3 diverged from its original sprint plan once it was confirmed CVC has no live Simpro API access yet. This document reflects what was actually built, sprint by sprint, and re-scopes what remains.

---

## 1. Status Summary

| Phase | Name | Status |
|---|---|---|
| 1 | Local AI Platform | ✅ Complete |
| 2 | Production RAG | ✅ Complete |
| 3 | Simpro API Integration | 🔶 In Progress — Sprint 4 of revised plan |
| 4 | Document Generation | ⏳ Blocked on Phase 3 sign-off |
| 5–9 | Security, Sales Agent, Tender Agent, Customer Intelligence, Multi-Agent | ⏳ Not started |

---

## 2. Phase 1 — Local AI Platform ✅

- Ubuntu Desktop 24.04 LTS
- Docker Compose
- Ollama (local LLM inference)
- Open WebUI

## 3. Phase 2 — Production RAG ✅

- PostgreSQL + PGVector (`pgvector/pgvector:0.8.6-pg16`)
- Apache Tika 3.3.1 for document extraction
- Ollama `nomic-embed-text` embeddings
- Hybrid search enabled in Open WebUI

---

## 4. Phase 3 — Simpro API Integration (Revised)

### 4.1 Why the original 6-sprint plan changed

The original plan (Sprint 1: foundation → Sprint 2: mock API → Sprint 3: core endpoints → Sprint 4: remaining endpoints + rate limiting → Sprint 5: error handling → Sprint 6: Docker + docs) assumed the typed client and its endpoint modules would be built early, tested against a thin mock.

In practice, CVC does not yet have Simpro Premium API access. Rather than build endpoint modules against untested assumptions about response shape, the team made an architecture decision (`docs/ADR/adr-mock-simpro-api.md`) to first build a **high-fidelity mock service** covering all 12 target resources, so that when live access arrives, only `SIMPRO_BASE_URL` changes — no client code changes. This was the right call, but it means the typed client layer (Pydantic models, endpoint modules, pagination, rate limiting) is later in the sequence than originally planned.

### 4.2 Actual Sprint History

**Sprint 1 — Client Foundation** ✅ Complete
- `simpro_client` package: `config.py` (pydantic-settings, `SIMPRO_` env prefix), `auth.py` (OAuth2 Client Credentials + API Key fallback, token caching/refresh), `client.py` (base httpx client, 401 retry), `exceptions.py` (typed hierarchy), `logging.py` (JSON logs, correlation IDs via `ContextVar`)
- 18 passing unit tests (`respx`-mocked, no live dependency)

**Sprint 2 — Architecture Pivot** ✅ Complete (folded into planning, not a separate build sprint)
- Decision recorded: mock-first strategy, Client Credentials grant for Phase 3 (Authorization Code Grant deferred to a future user-facing portal, Phase 6+)
- Two-company model confirmed: `CVC Service` (`company_id=1`), `CVC Projects` (`company_id=2`)

**Sprint 3 — Simpro Mock Service** ✅ Complete
- New service `simpro_mock` (FastAPI), backed by its own PostgreSQL container (`simpro-mock-db`, port 5433) — kept separate from the Phase 2 PGVector database
- 12 resources modelled and seeded: Companies, Customers, Jobs, Quotes, Contacts, Sites, Assets, Employees, Projects, JobNotes, Attachments, Statuses
- Bearer-token auth middleware, Simpro-style query filtering (`gt()`, `between()`, `search=all|any`), pagination headers (`Result-Total`, `Result-Count`, `Result-Pages`)
- Alembic migrations, Docker Compose service on port 8100
- ADR written: `adr-mock-simpro-api.md`

**Sprint 4 — Typed Client Layer** 🔶 In Progress (current)
- Adds the piece the original plan expected much earlier: typed Pydantic models + endpoint modules on `simpro_client`, now built against the completed Sprint 3 mock
- Scope: `models/` (12 resource models, PascalCase-aliased), `endpoints/` (generic `ResourceEndpoint`, wired per resource), `pagination.py` (lazy multi-page iterator), `rate_limiter.py` (token bucket, 8 req/sec per ADR-005), 429 retry-with-backoff in `client.py`, correlation-ID propagation as a request header
- Also fixes two test-suite defects found during Sprint 3 review: a script-style test file that broke pytest collection when the mock wasn't running, and helper functions accidentally named `test_*` that pytest tried to collect as tests
- Remaining before sign-off: endpoint-layer test coverage, full-suite regression run, `docs/phase3.md` refresh, git commit

**Sprint 5 — Hardening & Documentation** ⏳ Planned
- Full retry/error-handling review across all endpoints
- Finalise the outstanding ADR on the **Phase 3 → Phase 4 handoff mechanism** (direct Python import of `simpro_client` vs. a thin FastAPI service wrapper) — this must be decided before Phase 4 scoping begins
- Documentation suite refresh (architecture, installation, troubleshooting, CHANGELOG)

**Sprint 6 — Phase 4 Readiness Review** ⏳ Planned
- Confirm `simpro_client` is stable, importable, and covers every resource Phase 4 needs (Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees)
- Formal handover checklist signed off

### 4.3 Current Technology Stack (Phase 3)

| Component | Version | Notes |
|---|---|---|
| Python | 3.12.3 | Pinned, Ubuntu 24.04 default |
| httpx | 0.28.1 | `simpro_client` HTTP layer |
| pydantic | 2.13.4 | `simpro_client` models |
| pydantic-settings | 2.14.2 (`simpro_client`) / 2.15.0 (`simpro_mock`) | `.env`-driven config |
| pytest | 9.1.1 | |
| respx | 0.23.1 | httpx mocking for unit tests |
| ruff | 0.16.1 | Lint/format, line-length 88 |
| pytest-cov | 7.0.0 | |
| FastAPI | 0.141.1 | `simpro_mock` service |
| uvicorn | 0.52.4 | |
| SQLAlchemy | 2.0.52 | **Synchronous** (not async) |
| psycopg2-binary | 2.9.12 | Sync driver, matches SQLAlchemy mode |
| alembic | 1.19.1 | Schema migrations |
| postgres | 16-alpine | `simpro-mock-db` container, port 5433 |

---

## 5. Phase 4 — Document Generation (Blocked)

**Entry criteria (not yet met):**
1. Phase 3 Sprint 4 typed client layer signed off with test coverage
2. Phase 3 → Phase 4 handoff ADR finalised (direct import vs. endpoint)

**Planned scope (unchanged from original master document):**
- Consumes `simpro_client` directly as a Python library (per the library-first architecture decision)
- Key feeder endpoints: Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees
- Generates: Quotes, RAMS, Contracts, Equipment specifications, Tender responses, Technical documentation
- Phase 2 (PGVector knowledge base) is a candidate RAG source for boilerplate clauses/templates

---

## 6. Phases 5–9 (Unchanged)

Security & Reverse Proxy → AI Sales Agent → Public Tender Agent → Customer Intelligence → Multi-Agent Architecture, per the original master roadmap. No implementation work has started on these; scope as previously defined.

---

## 7. Engineering Standards (Unchanged, Reaffirmed)

- Docker-first, self-hosted, no cloud AI providers without explicit approval
- Python: PEP8, Black, Ruff, type hints, docstrings, structured logging, `.env` config
- SQLAlchemy 2.0 usage stays **synchronous** across `simpro_mock` — do not introduce `asyncpg`/async sessions without a dedicated ADR, since it would create a mismatch with the existing sync codebase
- Every service in Docker Compose with persistent volumes and restart policies
- One sprint at a time; each sprint ends with a git commit and a documentation update