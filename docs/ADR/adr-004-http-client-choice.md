# ADR-004: HTTP Client — httpx

## Status
Accepted (implemented, Phase 3 Sprint 1)

## Context
`simpro_client` needed an HTTP library to talk to the Simpro REST API (and, for now, the mock service standing in for it). The choice needed to support connection pooling, timeouts, a clean base-URL pattern, and a credible path to async use in later multi-agent phases, while also being easy to mock in unit tests.

## Decision
Use **httpx** (pinned `0.28.1`) as the HTTP client, via `httpx.Client` in `simpro_client/client.py` and `simpro_client/auth.py`.

## Alternatives Considered
- **`requests`** — rejected: no native async API (relevant for future Phase 9 multi-agent work), and no built-in `base_url` support as clean as httpx's.
- **`aiohttp`** — rejected: async-only; the rest of the codebase (including `simpro_mock`'s SQLAlchemy layer) is deliberately synchronous, and introducing async here would create an inconsistent mix without a corresponding decision to go async project-wide.

## Consequences
- Positive: `respx` provides first-class httpx mocking, which is what makes the 18-test offline unit suite possible with no live network dependency.
- Positive: `base_url` + default headers configured once on `SimproClient.__init__`, keeping `_request()` simple.
- Positive: async readiness is preserved for later phases without committing to it now — `httpx.AsyncClient` is a drop-in counterpart if a future ADR decides to go async.
- Neutral: version pinned at `0.28.1`; upgrades should be deliberate, not automatic, given the client is foundational to every future phase's Simpro access.
