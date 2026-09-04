# Phase 4 Project Design Document — Document Generation (Draft, Pre-Implementation)

**Status:** Draft — no code exists yet. This PDD captures the planned scope from `# CLIVE Enterprise AI Platform.txt` and `RevisedScope.txt` so planning is recorded before implementation starts, per the project's own "design before implementation" principle. It should be revisited and confirmed once Phase 3 signs off.

## 1. Objective

Generate CVC's core business documents — Quotes, RAMS, Contracts, Equipment specifications, Tender responses, Technical documentation — by combining structured business data from Simpro (via `simpro_client`) with unstructured boilerplate/templates/clauses retrieved from the Phase 2 knowledge base.

## 2. Entry Criteria (not yet met)

1. Phase 3's typed client layer (`simpro_client.models`, `simpro_client.endpoints`) signed off with test coverage.
2. The Phase 3 → Phase 4 handoff ADR finalised (direct import vs. thin service wrapper — see `docs/ADR/adr-006-phase3-phase4-handoff.md`, currently Proposed/open).

**Phase 4 should not begin implementation until both are satisfied.**

## 3. Scope (planned, subject to revision at Phase 4 kickoff)

**In scope:**
- Consume `simpro_client` as a Python library (pending the handoff ADR decision)
- Feeder data: Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees
- Generate: Quotes, RAMS (Risk Assessment Method Statements), Contracts, Equipment specifications, Tender responses, Technical documentation, Compliance documentation
- Use Phase 2's PGVector knowledge base as a RAG source for boilerplate clauses, templates, and case studies
- Output format(s): to be decided at kickoff — likely Word (`.docx`) and/or PDF, matching what CVC's clients expect to receive

**Out of scope (initial delivery, per the master roadmap):**
- Automated document delivery/e-signature workflows
- Fine-tuning a local model on CVC's own documentation (explicitly flagged as a *future* objective in the master document, not initial scope)
- Any write-back to Simpro (Phase 3 remains read-only)

## 4. Proposed Architecture

```
                     ┌───────────────────────────┐
                     │   Document Generation       │
                     │   Service (Phase 4)          │
                     └──────────┬──────────┬────────┘
                                │          │
                     (structured data)  (unstructured context)
                                │          │
                     ┌──────────▼───┐  ┌───▼─────────────────┐
                     │ simpro_client │  │  PGVector Knowledge  │
                     │ (Phase 3)     │  │  Base (Phase 2)       │
                     └──────────┬───┘  └───────────────────────┘
                                │
                     ┌──────────▼───┐
                     │ simpro-mock   │  (until live Simpro access
                     │ or live Simpro│   is enabled — see Phase 3)
                     └───────────────┘
```

This diagram assumes the "direct import" resolution of the handoff ADR; if the service-wrapper option is chosen instead, Document Generation would call a thin internal API rather than importing `simpro_client` directly. **This diagram must be corrected once the ADR is decided.**

## 5. Open Questions for Phase 4 Kickoff

1. Handoff mechanism (see §2) — blocking.
2. Output file format(s) and templating approach (e.g. Jinja2 → docx, or a docx-editing library against CVC templates).
3. Which Simpro resources are actually needed for a first-cut Quote/RAMS generator — full coverage of all 12 mock resources, or a smaller subset to start?
4. Whether generated documents need versioning/audit trail from day one, given the Knowledge Base's stated requirement for document versioning.
5. Whether real Simpro API access will be available by the time Phase 4 starts, or whether Phase 4 development will also proceed against `simpro-mock`.

## 6. Risks

| Risk | Notes |
|---|---|
| Phase 3's typed layer isn't built yet | Phase 4 cannot meaningfully start until `simpro_client.models`/`endpoints` exist |
| Handoff mechanism undecided | Building against an assumed mechanism (e.g. direct import) risks rework if the ADR resolves the other way |
| No real Simpro data validated yet | Document templates built against mock data may need adjustment once real payload shapes are confirmed |

## 7. Next Step

Do not schedule Phase 4 sprint planning until the two entry criteria in §2 are met. This PDD should be revisited (and likely substantially expanded with concrete sprint scoping) at that point.
