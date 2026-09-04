# ADR-009: Phase 3 → Phase 4 Handoff Mechanism

## Status
**Proposed — open decision.** This is the ADR flagged as a gap in `RevisedScope.txt` and `docs/PDD-phase3.md`. It has not been decided yet; this document lays out the options so a decision can be made and recorded before Phase 4 scoping begins, rather than defaulting to one silently.

## Context
Phase 4 (Document Generation) needs to read Simpro data (Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees) from `simpro_client`. ADR-006 already established a general library-first principle for `simpro_client`, but that decision was made before Phase 4's actual requirements were known. This ADR asks the same question specifically for the Phase 3 → Phase 4 boundary.

## Option A: Direct Python Import

Phase 4 code does `from simpro_client import SimproClient` (or the future typed endpoint modules) directly, in-process.

**Pros:**
- Zero network hop, zero extra container, zero extra auth boundary
- Shares process-level observability (correlation IDs, structured logs) automatically
- Consistent with ADR-006's existing library-first principle and the original Phase 3 PDD's stated architecture
- Simplest to build and test right now

**Cons:**
- Couples Phase 4 tightly to `simpro_client`'s Python API and versioning; any future non-Python consumer (e.g. a separate microservice, or an n8n/low-code workflow in a later phase) would need its own integration path
- If Phase 4 and Phase 3's code live in different deployable units later, direct import stops being an option without a refactor

## Option B: Thin FastAPI Service Wrapper

Wrap `simpro_client` in a small internal FastAPI service; Phase 4 calls it over HTTP, the same way it will eventually call the mock or real Simpro today.

**Pros:**
- Decouples Phase 4 from `simpro_client`'s internal Python API
- Opens the door to non-Python consumers later (e.g. Phase 6 AI Sales Agent, Phase 9 multi-agent orchestration, if those end up as separate services)
- Consistent internal API surface regardless of what's behind it (mock, real Simpro, or a future replacement)

**Cons:**
- Adds a container, a port, and an internal auth boundary for a need that doesn't exist yet — the exact "unnecessary complexity" ADR-006 originally argued against
- Correlation ID propagation and structured logging would need to be threaded across an additional HTTP hop
- No current consumer actually requires this — Phase 4 is Python, in the same codebase

## Recommendation (non-binding — for CVC's decision)

Given that every currently planned Phase 4 consumer is Python, and no cross-language or cross-service requirement has been identified yet, **Option A (direct import)** is consistent with the project's existing library-first decision (ADR-006) and its "no unnecessary complexity" principle. Option B can be introduced later, behind the same public interface, if a genuine non-Python or cross-service need materializes (for example, if a future phase is deployed as a separate service rather than sharing Phase 4's process).

## Decision
_Pending — to be filled in once confirmed._

## Consequences
_To be recorded once the decision above is made._
