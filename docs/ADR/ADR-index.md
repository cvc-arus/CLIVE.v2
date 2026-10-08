# Architecture Decision Records — Index

| # | Title | Phase | Status |
|---|---|---|---|
| 001 | Self-Hosted Local LLM Stack (Ollama + Open WebUI) | 1 | Accepted, implemented |
| 002 | Vector Database — PostgreSQL + PGVector | 2 | Accepted, implemented |
| 003 | Document Extraction — Apache Tika | 2 | Accepted, implemented |
| — | Mocking the Simpro REST API (`adr-mock-simpro-api.md`, pre-existing) | 3 | Accepted, implemented; "Capabilities & Coverage" superseded by ADR-013 |
| 004 | HTTP Client — httpx | 3 | Accepted, implemented |
| 005 | Auth Strategy — Client Credentials + API Key fallback | 3 | Accepted, implemented |
| 006 | Library-First Architecture for `simpro_client` | 3 | Accepted, implemented |
| 007 | Configuration Management — pydantic-settings | 3 | Accepted, implemented |
| 008 | Rate Limiting — token bucket at 8 req/sec | 3 | Withdrawn (duplicate of ADR-010) |
| 009 | Phase 3 → Phase 4 Handoff Mechanism | 3→4 | **Proposed, open decision — needs CVC sign-off** |
| 010 | Client-Side Resilience, Rate Limiting, and Error Handling | 3→4 | Accepted, implemented with deviations (see `src/simpro_client/CLAUDE.md`); §2.5 superseded by ADR-011 |
| 011 | Exception Hierarchy and Authentication Error Context (supersedes ADR-010 §2.5) | 3 | Accepted 2026-10-06, implemented |
| 012 | Retry Delay Ceiling and Token-Refresh Concurrency (supersedes ADR-010 §2.3, extends §2.1) | 3 | Accepted 2026-10-06 |
| 013 | Re-shape `simpro_mock` and `simpro_client` to Simpro's published API spec (supersedes `adr-mock-simpro-api.md` "Capabilities & Coverage") | 3 | Accepted 2026-10-07; **implemented** 2026-10-08 (all 7 sprints; conformance baseline empty, 50/50) |
