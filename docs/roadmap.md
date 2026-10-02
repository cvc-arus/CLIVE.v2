# CLIVE Roadmap

Consolidated from `docs/scope/master-project-document.md` (master roadmap) and `docs/scope/scope&readmap-rev2.md` (Phase 3 revision, formerly `RevisedScope.txt`), cross-checked against the codebase.

| Phase | Name | Status | Notes |
|---|---|---|---|
| 1 | Local AI Platform | ✅ Complete | Ollama + Open WebUI on Docker |
| 2 | Production RAG | ✅ Complete | PGVector + Tika + Hybrid Search |
| 3 | Simpro API Integration | 🔶 In progress | Client foundation, mock service and typed client layer implemented (`src/simpro_client/models/`, `endpoints/`, `rate_limiter.py`), with deviations from ADR-010 listed in `src/simpro_client/CLAUDE.md`. Not signed off; waiting on ADR-009 |
| 4 | Document Generation | ⏳ Blocked | Waiting on Phase 3 sign-off and the ADR-009 handoff decision |
| 5 | Security & Reverse Proxy | ⏳ Not started | Nginx, HTTPS, firewall, auth |
| 6 | AI Sales Agent | ⏳ Not started | Prospect discovery, lead scoring |
| 7 | Public Tender Agent | ⏳ Not started | Tender monitoring & bid analysis |
| 8 | Customer Intelligence | ⏳ Not started | ICP generation, customer analytics |
| 9 | Multi-Agent Architecture | ⏳ Not started | Orchestrated AI workflows |
| 10 | Monitoring & Disaster Recovery | ⏳ Not started | Backups (Phase 2 partially covers this), health monitoring |

## Phase 3 — Remaining Work

1. **Decide the Phase 3 → Phase 4 handoff** — drafted as ADR-009 (`docs/ADR/adr-009-phase3-phase4-handoff.md`, Proposed, open): direct `import simpro_client` (library-first) vs. a thin FastAPI service wrapper. This is a hard gate before Phase 4 scoping.
2. **Sign off Phase 3** once ADR-009 is accepted. The typed layer has offline tests: `tests/test_models.py`, `test_endpoints.py`, `test_pagination.py`, `test_rate_limiter.py`, `test_retries.py`, `test_route_contract.py`.

Done:
- Typed client layer: `src/simpro_client/models/` (Pydantic, PascalCase-aliased, one module per resource) and `src/simpro_client/endpoints/` (generic `ResourceEndpoint` in `base.py` plus per-resource modules).
- Pagination: `fetch_page()` and `iter_all()` in `src/simpro_client/endpoints/base.py` (there is no separate `pagination.py`).
- Rate limiter: `src/simpro_client/rate_limiter.py` (token bucket, default 8 req/sec), per ADR-010.
- Legacy `tests/test_simpro_mock.py` removed; `structure.txt` regenerated from tracked files.

## Phase 4 Entry Criteria (unchanged from `docs/scope/scope&readmap-rev2.md`)

1. Phase 3 typed client layer signed off with test coverage.
2. Phase 3 → Phase 4 handoff ADR (ADR-009) finalised.

## Phase 4 Planned Scope (unchanged from the master roadmap, `docs/scope/master-project-document.md`)

- Consumes `simpro_client` directly as a Python library
- Feeder endpoints: Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees
- Generates: Quotes, RAMS, Contracts, Equipment specifications, Tender responses, Technical documentation
- Phase 2's PGVector knowledge base is a candidate RAG source for boilerplate clauses/templates

## Phases 5–9

Unchanged from the original master document (`docs/scope/master-project-document.md`): Security & Reverse Proxy → AI Sales Agent → Public Tender Agent → Customer Intelligence → Multi-Agent Architecture. No implementation has started on any of these.
