# ADR-016: Conversational access approach for Simpro data

- **Status:** Proposed
- **Date:** 2026-10-09
- **Deciders:** Alex
- **Related:** ADR-014, ADR-015

## Context

Users will ask natural-language questions about Simpro data in Open WebUI.
The local LLM (Ollama, RTX 3080 10 GB) needs a way to obtain the data required
to answer accurately, while respecting ADR-015 access control.

## Options considered

### Option A — Tool calling over a fixed query catalogue
An Open WebUI tool calls `clive-gateway` endpoints, each a read-only,
parameterised query. The model selects the query and arguments; Python computes
the results.
- Pro: live data; permissions enforced per query; each query testable.
- Pro: arithmetic and aggregation done in code, not by the model.
- Con: only catalogue questions can be answered; the catalogue grows over time.

### Option B — Text-to-SQL over a synced copy
The model writes SQL against a replicated Simpro dataset.
- Pro: flexible, in theory.
- Con: small local models produce plausible but wrong SQL.
- Con: needs a sync/caching layer (previously out of scope).
- Con: row and field restrictions are hard to guarantee over arbitrary SQL.
- Con: built against the mock schema, which is not guaranteed to match real Simpro.

### Option C — Embed Simpro records in the PGVector knowledge base
- Pro: easiest to wire up.
- Con: stale immediately; RAG cannot count, total or filter reliably.
- Con: no per-user filtering in the knowledge base, so it bypasses ADR-015 entirely.

## Decision

**Option A.** Options B and C are rejected. Simpro data must never be written
to the PGVector knowledge base.

## Consequences

- Sprint 1 of Phase 3B must produce a query catalogue from real user questions.
- Unsupported questions are logged during the pilot to drive catalogue v2.
- The chosen model must handle tool calls reliably; a model evaluation is part
  of Sprint 1.
- Query results are capped and summarised before reaching the model.

## Revisit if

- Users consistently need questions the catalogue cannot reasonably cover.
- Hardware upgrade makes much larger models practical.
