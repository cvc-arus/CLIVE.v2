# ADR-009: Phase 3 → Phase 4 handoff mechanism

- **Status:** Proposed
- **Date:** 2026-10-09
- **Deciders:** Alex
- **Related:** ADR-010 (resilience policy / rate limiter), ADR-011 (Simpro data access control model, proposed)

## Context

Phase 3 delivers `simpro_client`, a typed Python library for the Simpro REST API.
This ADR decides how downstream consumers access Simpro data.

A new requirement (October 2026) changes the consumer landscape: any authorised
CVC user must be able to ask questions about Simpro data in Open WebUI, with
access restricted by role. Consumers are now:

1. Open WebUI tools (run inside the `open-webui` container; no `simpro_client` install)
2. Phase 4 document generation (user-triggered and batch)
3. Future agents (Phases 6–9)

Constraints:
- Simpro's rate limit (10 req/sec) is shared across the whole build.
- The ADR-010 token bucket (8 req/sec) is enforced per process.
- Simpro data must be filtered by user role before reaching any LLM.

## Options considered

### Option A — Direct Python import
Each consumer imports `simpro_client` and calls Simpro itself.
- Pro: simplest; typed objects end to end; no extra service.
- Con: unusable by Open WebUI tools without installing the library into a
  third-party container.
- Con: each process has its own rate limiter, so combined traffic can exceed
  the shared Simpro limit.
- Con: permissions and audit must be re-implemented per consumer, or are bypassed.

### Option B — Gateway service as the single Simpro access point
A FastAPI service (`clive-gateway`) imports `simpro_client` and exposes
permission-checked, audited query endpoints. All other consumers use its HTTP API.
- Pro: one rate limiter, one permission model, one audit trail.
- Pro: language/container agnostic; serves Open WebUI, Phase 4 and agents alike.
- Con: additional service and single point of failure for Simpro access.
- Con: requires a versioned API contract; consumers receive JSON, not Pydantic objects.

## Decision

**Option B.** `simpro_client` is imported directly by exactly one runtime
service, `clive-gateway`. All other CLIVE components access Simpro data only
through the gateway's HTTP API.

Exceptions: unit/integration tests and developer tooling against the mock.
Any other direct import requires an amendment to this ADR.

## Consequences

- The gateway runs as a **single uvicorn worker** so the ADR-010 rate limiter
  remains authoritative. Scaling beyond one worker requires a shared limiter
  (new ADR).
- The gateway supports **service accounts** (e.g. a `docgen` role for Phase 4
  batch jobs) alongside human users; both are subject to the same policy and audit.
- The gateway's OpenAPI schema is the contract for consumers; breaking changes
  require a versioned path (`/v1/`, `/v2/`).
- `simpro_client` remains a pure Simpro library with no knowledge of CLIVE
  users or permissions.
- Phase 4 is unblocked by this decision; its entry criteria now include the
  gateway's query catalogue covering Customers, Sites, Contacts, Jobs, Quotes,
  Projects, Assets and Employees.

## Revisit if
- The gateway becomes a measurable bottleneck.
- A consumer needs bulk data access that per-query endpoints can't serve
  efficiently (e.g. analytics for Customer Intelligence, Phase 8).