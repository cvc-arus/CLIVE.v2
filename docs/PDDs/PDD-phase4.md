# Phase 4 Project Design Document — Document Generation (Draft, Pre-Implementation)

**Status:** Draft — no code exists yet. This PDD captures the planned scope from `docs/scope/master-project-document.md` and `docs/scope/scope-rev2.md` so planning is recorded before implementation starts, per the project's own "design before implementation" principle. It should be revisited and confirmed once Phase 3 signs off.

## 1. Objective

Generate CVC's core business documents — Quotes, RAMS, Contracts, Equipment specifications, Tender responses, Technical documentation — by combining structured business data from Simpro (via `clive-gateway`'s HTTP API, ADR-009) with unstructured boilerplate/templates/clauses retrieved from the Phase 2 knowledge base.

## 2. Entry Criteria

1. Phase 3's typed client layer (`simpro_client.models`, `simpro_client.endpoints`) signed off with test coverage.
2. The Phase 3 → Phase 4 handoff ADR finalised. ADR-009's decision was recorded on 2026-10-09 (Alex): Option B, a single `clive-gateway` service imports `simpro_client` and serves every other consumer, including Phase 4, over HTTP (`docs/ADR/adr-009-phase3-phase4-handoff.md`).
3. `clive-gateway`'s query catalogue covers Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets and Employees (ADR-009, Consequences). `clive-gateway` does not exist yet; it is planned in Phase 3B (`PDD-phase3b-simpro-conversational-access.md`).

Whether each criterion is met is recorded in `docs/STATUS.md`. **Phase 4 should not begin implementation until all three are satisfied.**

## 3. Scope (planned, subject to revision at Phase 4 kickoff)

**In scope:**
- Consume Simpro data through `clive-gateway`'s HTTP API (ADR-009); Phase 4 does not import `simpro_client`
- Authenticate to the gateway as the `docgen` service account (Phase 3B PDD §7.4), with access to both companies and the resources and field classifications Phase 4 needs, under the same deny-by-default access control model as human users (ADR-014, Proposed)
- Feeder data: Customers, Sites, Contacts, Jobs, Quotes, Projects, Assets, Employees
- Generate: Quotes, RAMS (Risk Assessment Method Statements), Contracts, Equipment specifications, Tender responses, Technical documentation, Compliance documentation
- Use Phase 2's PGVector knowledge base as a RAG source for boilerplate clauses, templates, and case studies
- Output format(s): to be decided at kickoff — likely Word (`.docx`) and/or PDF, matching what CVC's clients expect to receive

**Out of scope (initial delivery, per the master roadmap):**
- Automated document delivery/e-signature workflows
- Fine-tuning a local model on CVC's own documentation (explicitly flagged as a *future* objective in the master document, `docs/scope/master-project-document.md`, not initial scope)
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
                           HTTP │          │
                     ┌──────────▼───┐  ┌───▼─────────────────┐
                     │ clive-gateway │  │  PGVector Knowledge  │
                     │ (ADR-009)     │  │  Base (Phase 2)       │
                     └──────────┬───┘  └───────────────────────┘
                                │ imports
                     ┌──────────▼───┐
                     │ simpro_client │
                     │ (Phase 3)     │
                     └──────────┬───┘
                                │
                     ┌──────────▼───┐
                     │ simpro-mock   │  (until live Simpro access
                     │ or live Simpro│   is enabled — see Phase 3)
                     └───────────────┘
```

Corrected for ADR-009's decision (2026-10-09): Document Generation calls `clive-gateway` over HTTP and never imports `simpro_client`; the gateway is the only runtime service that does. `clive-gateway` is planned in Phase 3B and does not exist yet.

## 5. Open Questions for Phase 4 Kickoff

1. Handoff mechanism — resolved by ADR-009 (2026-10-09): through `clive-gateway`.
2. Output file format(s) and templating approach (e.g. Jinja2 → docx, or a docx-editing library against CVC templates).
3. Which Simpro resources are actually needed for a first-cut Quote/RAMS generator — full coverage of all 12 mock resources, or a smaller subset to start?
4. Whether generated documents need versioning/audit trail from day one, given the Knowledge Base's stated requirement for document versioning.
5. Whether real Simpro API access will be available by the time Phase 4 starts, or whether Phase 4 development will also proceed against `simpro-mock`.

## 6. Risks

| Risk | Notes |
|---|---|
| Phase 3's typed layer isn't built yet | Phase 4 cannot meaningfully start until `simpro_client.models`/`endpoints` exist |
| Phase 4 depends on `clive-gateway` | The handoff is decided (ADR-009), but the gateway and its query catalogue are planned in Phase 3B and do not exist yet |
| No real Simpro data validated yet | Document templates built against mock data may need adjustment once real payload shapes are confirmed |

## 7. Next Step

Do not schedule Phase 4 sprint planning until the two entry criteria in §2 are met. This PDD should be revisited (and likely substantially expanded with concrete sprint scoping) at that point.
