# CLIVE Roadmap

Consolidated from `docs/scope/master-project-document.md` (master roadmap) and `docs/scope/scope-rev2.md` (Phase 3 revision, formerly `RevisedScope.txt`), cross-checked against the codebase.

> **Status lives in [`STATUS.md`](STATUS.md)** (sole owner since 2026-10-13). This file owns the phase list and scope only.

| Phase | Name | Status | Notes |
|---|---|---|---|
| 1 | Local AI Platform | [See `STATUS.md`](STATUS.md) | Ollama + Open WebUI on Docker |
| 2 | Production RAG | [See `STATUS.md`](STATUS.md) | PGVector + Tika + Hybrid Search |
| 3 | Simpro API Integration | [See `STATUS.md`](STATUS.md) | Client foundation, mock service and typed client layer implemented (`src/simpro_client/models/`, `endpoints/`, `rate_limiter.py`), with deviations from ADR-010 listed in `src/simpro_client/CLAUDE.md`. Shaped to Simpro's published contract and proved by `tests/test_spec_conformance.py` (ADR-013). Closed by Alex once ADR-009 was decided. Live Simpro API access arrived 2026-10-16 and is used read-only (root `CLAUDE.md` §3) |
| 3B | Simpro Conversational Access | [See `STATUS.md`](STATUS.md) | Role-restricted Simpro Q&A in Open WebUI through `clive-gateway` (ADR-009, ADR-014, ADR-015). Added October 2026; see "Phase 3B Planned Scope" below. Order relative to Phase 4: see `STATUS.md` |
| 4 | Document Generation | [See `STATUS.md`](STATUS.md) | Entry criteria include `clive-gateway`'s query catalogue (Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees) |
| 5 | Security & Reverse Proxy | [See `STATUS.md`](STATUS.md) | Nginx, HTTPS, firewall, auth. A minimum slice (Nginx + HTTPS, LAN-only firewall, Open WebUI hardening) is planned in Phase 3B Sprint 2 |
| 6 | AI Sales Agent | [See `STATUS.md`](STATUS.md) | Prospect discovery, lead scoring |
| 7 | Public Tender Agent | [See `STATUS.md`](STATUS.md) | Tender monitoring & bid analysis |
| 8 | Customer Intelligence | [See `STATUS.md`](STATUS.md) | ICP generation, customer analytics |
| 9 | Multi-Agent Architecture | [See `STATUS.md`](STATUS.md) | Orchestrated AI workflows |
| 10 | Monitoring & Disaster Recovery | [See `STATUS.md`](STATUS.md) | Backups (Phase 2 partially covers this), health monitoring |

## Phase 3 — Closed 2026-10-09

Closed by Alex once ADR-009 was decided. Both gates its sign-off waited on are
met: the handoff decision is recorded (ADR-009, Option B — a single
`clive-gateway` service imports `simpro_client` and serves every other consumer
over HTTP), and the open defects were triaged.

Two items carried past the close, neither a defect in the delivered code, both
in `known-issues.md`: the `pip install -e ".[dev]"` pitfall, which is a
consequence of PEP 735 `[dependency-groups]` and is handled by using `uv sync`
everywhere; and the pre-existing lint debt, which was cleared on 2026-10-12
(PR #47).

Four mock behaviours were **unverifiable without live credentials**; live
access arrived on 2026-10-16 and they are the first things to check (W1): whether Simpro returns `ID` in a
`columns` projection that did not ask for it, whether the `Result-Total` /
`Result-Count` / `Result-Pages` headers exist (they are real and documented but
absent from the published spec), `limit`'s exact semantics, and `/companies/`
being unpaginated upstream where the mock pages it.

The typed layer's tests: `tests/test_models.py`, `test_endpoints.py`,
`test_pagination.py`, `test_rate_limiter.py`, `test_retries.py`,
`test_route_contract.py` and `test_spec_conformance.py` offline, plus two
integration modules, `test_simpro_mock_v2.py` and `test_client_mock_drift.py`.

Delivered:
- Contract conformance (ADR-013, implemented 2026-10-08): `simpro_mock` and `simpro_client` are shaped to Simpro's published OpenAPI contract, vendored at `docs/contracts/simpro-openapi-v1-get-subset.json`. `tests/test_spec_conformance.py` validates every client model against payloads generated from it and `tests/spec_conformance_baseline.json` is empty, so "switching to live Simpro is a configuration change" is measured rather than asserted.
- Typed client layer: `src/simpro_client/models/` (Pydantic, PascalCase-aliased, one module per resource) and `src/simpro_client/endpoints/` (generic `ResourceEndpoint` in `base.py` plus per-resource modules).
- Pagination: `fetch_page()` and `iter_all()` in `src/simpro_client/endpoints/base.py` (there is no separate `pagination.py`).
- Rate limiter: `src/simpro_client/rate_limiter.py` (token bucket, default 8 req/sec), per ADR-010.
- Legacy `tests/test_simpro_mock.py` removed; `structure.txt` regenerated from tracked files.

## Phase 3B Planned Scope (`docs/PDDs/PDD-phase3b-simpro-conversational-access.md`)

Simpro conversational access was not in the original scope or Revision 2; it
was added in October 2026. "3B" places it after Phase 3 and before Phase 4
without renumbering later phases. None of it exists yet.

- `clive-gateway`: the single runtime importer of `simpro_client` (ADR-009), with a deny-by-default, role-based access control model and audit log (ADR-014, Proposed)
- An Open WebUI tool that answers questions through a fixed catalogue of read-only queries (ADR-015, Proposed); no free-form text-to-SQL, and Simpro data is never written to the PGVector knowledge base
- The minimum security slice from Phase 5 (Nginx + HTTPS, LAN-only firewall, Open WebUI hardening)
- Planned schedule: six sprints over about nine weeks of full-time effort (PDD §12–§13). Entry criteria include completing the course correction sprint (PDD §5)
- Order relative to Phase 4: decided at the end of the course correction sprint; see `STATUS.md`

## Phase 4 Entry Criteria (unchanged from `docs/scope/scope-rev2.md`)

1. Phase 3 typed client layer signed off with test coverage.
2. Phase 3 → Phase 4 handoff ADR (ADR-009) finalised.

**Both met as of 2026-10-09.** ADR-009's decision adds a third, from its own
Consequences: `clive-gateway`'s query catalogue must cover Customers, Sites,
Contacts, Jobs, Quotes, Projects, Assets and Employees. The gateway does not
exist yet.

## Phase 4 Planned Scope (unchanged from the master roadmap, `docs/scope/master-project-document.md`)

- Consumes Simpro data **through `clive-gateway`'s HTTP API**, not by importing `simpro_client` (ADR-009, decided 2026-10-09; the gateway is the one service that imports the library)
- Feeder endpoints: Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees
- Generates: Quotes, RAMS, Contracts, Equipment specifications, Tender responses, Technical documentation
- Phase 2's PGVector knowledge base is a candidate RAG source for boilerplate clauses/templates

## Phases 5–9

Unchanged from the original master document (`docs/scope/master-project-document.md`): Security & Reverse Proxy → AI Sales Agent → Public Tender Agent → Customer Intelligence → Multi-Agent Architecture. No implementation has started on any of these.
