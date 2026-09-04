# CLIVE Roadmap

Consolidated from `# CLIVE Enterprise AI Platform.txt` (master roadmap) and `RevisedScope.txt` (Phase 3 revision), cross-checked against the codebase.

| Phase | Name | Status | Notes |
|---|---|---|---|
| 1 | Local AI Platform | ✅ Complete | Ollama + Open WebUI on Docker |
| 2 | Production RAG | ✅ Complete | PGVector + Tika + Hybrid Search |
| 3 | Simpro API Integration | 🔶 In progress | Client foundation + mock service complete (verified by running tests); typed models/endpoints layer not started in code |
| 4 | Document Generation | ⏳ Blocked | Waiting on Phase 3 typed client layer + handoff ADR |
| 5 | Security & Reverse Proxy | ⏳ Not started | Nginx, HTTPS, firewall, auth |
| 6 | AI Sales Agent | ⏳ Not started | Prospect discovery, lead scoring |
| 7 | Public Tender Agent | ⏳ Not started | Tender monitoring & bid analysis |
| 8 | Customer Intelligence | ⏳ Not started | ICP generation, customer analytics |
| 9 | Multi-Agent Architecture | ⏳ Not started | Orchestrated AI workflows |
| 10 | Monitoring & Disaster Recovery | ⏳ Not started | Backups (Phase 2 partially covers this), health monitoring |

## Phase 3 — Remaining Work

1. **Decide and record the Phase 3 → Phase 4 handoff ADR** — direct `import simpro_client` (library-first, matches the original architecture decision) vs. a thin FastAPI service wrapper. This is a hard gate before Phase 4 scoping.
2. **Build the typed client layer**: `simpro_client/models/` (Pydantic, PascalCase-aliased, one module per resource) and `simpro_client/endpoints/` (a generic `ResourceEndpoint` plus per-resource wiring), matching the shape already proven by the mock service.
3. **Add `pagination.py`** — a lazy, multi-page iterator over the mock's (and eventually real Simpro's) `page`/`pageSize`/`Result-Pages` contract.
4. **Add `rate_limiter.py`** — token bucket at 8 req/sec (per the original ADR-005 recommendation), since the mock does not itself enforce or simulate `429` responses.
5. **Housekeeping**: remove the legacy `tests/test_simpro_mock.py`, regenerate `structure.txt`, reconcile `RevisedScope.txt`'s sprint narrative with what's actually in the code (see `docs/known-issues.md`).
6. **Sign off Phase 3** once the typed layer has its own test coverage and the handoff ADR is accepted.

## Phase 4 Entry Criteria (unchanged from `RevisedScope.txt`)

1. Phase 3 typed client layer signed off with test coverage.
2. Phase 3 → Phase 4 handoff ADR finalised.

## Phase 4 Planned Scope (unchanged from the master roadmap)

- Consumes `simpro_client` directly as a Python library
- Feeder endpoints: Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees
- Generates: Quotes, RAMS, Contracts, Equipment specifications, Tender responses, Technical documentation
- Phase 2's PGVector knowledge base is a candidate RAG source for boilerplate clauses/templates

## Phases 5–9

Unchanged from the original master document (`# CLIVE Enterprise AI Platform.txt`): Security & Reverse Proxy → AI Sales Agent → Public Tender Agent → Customer Intelligence → Multi-Agent Architecture. No implementation has started on any of these.
