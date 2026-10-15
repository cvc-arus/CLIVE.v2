# Architecture Decision Records — Index

| # | Title | Phase | Status |
|---|---|---|---|
| 001 | Self-Hosted Local LLM Stack (Ollama + Open WebUI) | 1 | Accepted, implemented |
| 002 | Vector Database — PostgreSQL + PGVector | 2 | Accepted, implemented |
| 003 | Document Extraction — Apache Tika | 2 | Accepted, implemented |
| — | Mocking the Simpro REST API (`adr-mock-simpro-api.md`, pre-existing) | 3 | Accepted, implemented; "Capabilities & Coverage" superseded by ADR-013 |
| 004 | HTTP Client — httpx | 3 | Accepted, implemented |
| 005 | Auth Strategy — Client Credentials (Default) + API Key Fallback | 3 | Accepted, implemented |
| 006 | Library-First Architecture for `simpro_client` | 3 | Accepted, implemented; **"no service wrapper" partially superseded by ADR-009** |
| 007 | Configuration Management — pydantic-settings | 3 | Accepted, implemented |
| 008 | Client-Side Resilience, Rate Limiting, and Error Handling (`adr-008-rate-limiting-strategy.md`) | 3 | Withdrawn 2026-09-29 (duplicate of ADR-010) |
| 009 | Phase 3 → Phase 4 Handoff Mechanism | 3→4 | **Decision recorded 2026-10-09 (Alex): Option B, a single `clive-gateway` service.** Status line still reads Proposed; `clive-gateway` not built yet |
| 010 | Client-Side Resilience, Rate Limiting, and Error Handling | 3 | Approved, implemented with deviations (see `src/simpro_client/CLAUDE.md`); §2.5 superseded by ADR-011; §2.3 superseded and §2.1 extended by ADR-012 |
| 011 | Exception Hierarchy and Authentication Error Context (supersedes ADR-010 §2.5) | 3 | Accepted 2026-10-06, implemented |
| 012 | Retry Delay Ceiling and Token-Refresh Concurrency (supersedes ADR-010 §2.3, extends §2.1) | 3 | Accepted 2026-10-06 |
| 013 | Re-shape `simpro_mock` and `simpro_client` to Simpro's published API spec (supersedes `adr-mock-simpro-api.md` "Capabilities & Coverage") | 3 | Accepted 2026-10-07; **implemented** 2026-10-08 (all 7 sprints; conformance baseline empty, 50/50) |
| 014 | Simpro Data Access Control Model (`adr-014-simpro-access-control-model.md`) | 3B | Proposed (2026-10-09). `clive_gateway` storage on the Phase 2 Postgres vs root `CLAUDE.md` §3: resolved by Alex 2026-10-15 (narrow exception in §3) |
| 015 | Conversational Access Approach for Simpro Data (`adr-015-conversational-access-approach.md`) | 3B | Proposed (2026-10-09) |

**Next free number:** ADR-016

## Naming convention

| Rule | Example |
|---|---|
| File name: `adr-NNN-short-kebab-title.md`, lowercase, number zero-padded to three digits | `adr-014-simpro-access-control-model.md` |
| Heading: `# ADR-NNN: Title` | `# ADR-014: Simpro data access control model` |
| References in any document: `ADR-NNN` | "per ADR-010" |

Exceptions kept for existing links: `ADR-index.md` (this file) and the
unnumbered legacy `adr-mock-simpro-api.md`. Renaming either needs Alex's approval.

## Numbering rules

1. **Next number = highest number in this index + 1.** Check this index, the
   `docs/ADR/` folder and open branches or pull requests before assigning.
2. **Assign the number at commit time, in the repo.** Drafts written outside
   the repo (e.g. in a Claude chat) use the placeholder `ADR-XXX` in the file
   name, heading and references. Claude Code replaces it with the next free
   number when committing, and updates every reference.
3. **Reserve the number in the same commit:** add the index row with the ADR file.
4. **Numbers are never reused.** Withdrawn and superseded ADRs keep their file
   and number, with their status updated.
5. **Accepted ADRs are not rewritten.** Change them with a new ADR that
   supersedes them, and update only the old ADR's Status line
   (`docs/CLAUDE.md` §4).

## Statuses

`Proposed` · `Accepted` / `Approved` · `Superseded by ADR-NNN` · `Rejected` ·
`Withdrawn` (with a reason), as in `docs/CLAUDE.md` §4.
Only Alex changes a status to `Accepted`.
