# W3 — Knowledge Base Audit

| | |
|---|---|
| **Template** | Short (read-only review; any fixes become a separate sprint) |
| **Status** | Approved |
| **Depends on** | W5 complete (backups exist before inspecting live data) |
| **Related** | Phase 2 docs, ADR-001 (pgvector), ADR-002 (Tika) — confirm numbers in ADR index |

## Goal

Check whether the Phase 2 knowledge base meets the scope's requirements before
~5,000 documents go in: metadata, versioning, and access restriction for
sensitive documents. Re-ingesting everything later is far more expensive.

**Bulk ingestion is paused until this audit is accepted.**

## Tasks

### T1 — Current state (read-only)
1. Open WebUI version and RAG settings (embedding model, chunk size/overlap,
   hybrid search, top-k, reranking) from configuration and environment
   variable **names** (no secret values).
2. Counts: knowledge collections, files, chunks/vectors in pgvector.
3. How Open WebUI stores files, chunks and metadata: inspect the database
   tables and columns related to files, knowledge and vectors (schema and row
   counts only; do not dump document content).
4. Which metadata is currently stored per document and per chunk.
**Stop point:** findings written to `docs/reviews/kb-audit-2026-10.md` section 1.

### T2 — Requirement tests
Test in a **scratch collection** (create and later delete with Alex's approval):
1. **Metadata:** can a document carry custom metadata (type, customer, date,
   author), and can retrieval filter on it?
2. **Versioning:** upload v1, then v2 of the same document. Do v1 chunks remain
   searchable? Can v1 be retrieved deliberately?
3. **Access restriction:** can a collection be limited to a user group, and
   does a user outside the group get any of its content in answers?
4. **Deletion:** after deleting a document, are its vectors removed from pgvector?
**Stop point:** pass/fail per test with evidence.

### T3 — [HUMAN + Claude Code] Extraction spot-check
Alex selects ~10 representative files: tender PDF with tables, RAMS, contract,
scanned certificate, equipment datasheet, drawing. Claude Code runs them
through Tika (the existing container), and records extracted text quality:
tables intact, headings kept, scanned text present, drawings readable.
**Stop point:** quality table per file.

### T4 — Gap report and options
Complete `docs/reviews/kb-audit-2026-10.md` with:
- Requirements vs findings (met / partly / not met)
- Options: **Keep** as is · **Extend** Open WebUI's RAG with a metadata and
  version layer · **Own the pipeline** (CLIVE ingestion service writing to
  pgvector, Open WebUI as front end) · extraction improvements for tables,
  scans and drawings
- Effort and risk per option; recommendation (non-binding)
- Draft ADR if an architectural change is recommended
**Stop point:** report for Alex's decision.

## Verification
Report sections 1–4 complete; scratch collection removed (with approval).

## Rollback
Documentation only: `git revert`. Scratch collection deletion is the only data change.

## Git commit
`docs(review): knowledge base audit against metadata, versioning and access requirements`

## Acceptance criteria
- [ ] Current state documented
- [ ] Four requirement tests run with evidence
- [ ] Extraction quality recorded for representative files
- [ ] Gap report with options and recommendation
- [ ] `STATUS.md` updated (including whether bulk ingestion may resume)
