# Architecture Decision Records — Index

Place these files in `docs/ADR/` alongside the existing `adr-mock-simpro-api.md`.

| # | Title | Phase | Status |
|---|---|---|---|
| 001 | Self-Hosted Local LLM Stack (Ollama + Open WebUI) | 1 | Accepted, implemented |
| 002 | Vector Database — PostgreSQL + PGVector | 2 | Accepted, implemented |
| 003 | Document Extraction — Apache Tika | 2 | Accepted, implemented |
| — | Mocking the Simpro REST API (`adr-mock-simpro-api.md`, pre-existing) | 3 | Accepted, implemented |
| 004 | HTTP Client — httpx | 3 | Accepted, implemented |
| 005 | Auth Strategy — Client Credentials + API Key fallback | 3 | Accepted, implemented |
| 006 | Library-First Architecture for `simpro_client` | 3 | Accepted, implemented |
| 007 | Configuration Management — pydantic-settings | 3 | Accepted, implemented |
| 008 | Rate Limiting — token bucket at 8 req/sec | 3 | **Proposed, not yet implemented** |
| 009 | Phase 3 → Phase 4 Handoff Mechanism | 3→4 | **Proposed, open decision — needs CVC sign-off** |

Two items need your attention, not just filing:
- **ADR-008** describes a rate limiter that was planned but never built. `SimproRateLimitError` is ready for it, but nothing raises it from client-side enforcement yet.
- **ADR-009** is a genuine open decision (direct import vs. service wrapper for Phase 4). I've laid out both options with a non-binding recommendation, but this is the one that needs an actual answer from you before Phase 4 scoping starts — everything else in this batch documents decisions already made in code.
