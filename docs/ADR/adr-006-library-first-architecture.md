# ADR-006: Library-First Architecture for `simpro_client`

## Status
Accepted (implemented, Phase 3)

## Context
Future phases (starting with Phase 4, Document Generation) need to read Simpro data. The integration could be built as a Python library that consuming phases import directly, or as a standalone service (e.g. a FastAPI wrapper) that other phases call over HTTP.

## Decision
Build `simpro_client` as an **importable Python package** (`pip install -e .`, `from simpro_client import SimproClient`) with no service wrapper for now. Add a thin service wrapper later only if/when a non-Python consumer needs access.

## Alternatives Considered
- **Service-first (FastAPI wrapper around `simpro_client` from day one)** — rejected for the initial delivery: adds Docker/network overhead (another container, another port, another auth boundary) before any consumer actually needs it. Every currently planned consumer (Phase 4 Document Generation) is Python.
- **Both simultaneously** — rejected as premature; violates the project's "no unnecessary complexity" principle. Can be added later without breaking the library's public interface.

## Consequences
- Positive: Phase 4 (and later phases) can `import simpro_client` with zero network hop, zero extra container, and share the same process/observability (correlation IDs, structured logs) as the caller.
- Positive: defers a real architectural cost (a service boundary, its own auth, its own deployment) until there's a concrete need for it.
- **Open follow-on decision:** whether Phase 4 specifically uses direct import, or whether the passage of time / new requirements has changed the calculus, is being tracked separately as `docs/ADR/adr-009-phase3-phase4-handoff.md` (currently Proposed, not yet finalised). This ADR (006) records the general library-first principle; ADR-009 will record the specific Phase 3 → Phase 4 decision.
