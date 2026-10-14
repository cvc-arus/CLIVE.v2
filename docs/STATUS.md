# CLIVE — Status

> Single source of truth for current status. Update after every completed task
> (`/status-update`). Keep this file short: history belongs in `docs/CHANGELOG.md`,
> decisions in `docs/ADR/`.

**Last updated:** 2026-10-14

## Phases

Phase list and scope: `docs/roadmap.md`.

| Phase | Name | Status |
|---|---|---|
| 1 | Local AI Platform | ✅ Complete |
| 2 | Production RAG | ✅ Complete (knowledge base audit planned — W3) |
| 3 | Simpro API Integration | ✅ Closed 2026-10-09 (Alex). Evidence: `docs/phase3/phase3-signoff.md` |
| — | Course correction sprint | 🔶 In progress |
| 3B | Simpro Conversational Access | 📝 Planned — PDD drafted; order set at decision point |
| 4 | Document Generation (4A / 4B split pending W2) | ⏳ Not started; no longer blocked (ADR-009 decided) |
| 5 | Security & Reverse Proxy (minimum slice moves into 3B) | ⏳ Not started |
| 6–9 | Sales Agent, Tender Agent, Customer Intelligence, Multi-Agent | ⏳ Not started |
| 10 | Monitoring & Disaster Recovery (backups moved to W5) | ⏳ Not started |

## Current sprint: Course correction

Plan: `docs/course-correction-plan.md` · Tasks: `docs/sprints/course-correction/`

| Workstream | Status | Notes |
|---|---|---|
| W1 Simpro access and sandbox | ⏳ Not started | |
| W2 Doc generation value check | ⏳ Not started | |
| W3 Knowledge base audit | ⏳ Not started | Bulk ingestion paused until complete |
| W4 Evaluation set | ⏳ Not started | |
| W5 Backups and restore drill | 🔶 In progress | T1: all data on sdb1; target `<home>/clive-backups/` (sda2). T2: inventory agreed. See `docs/recovery-plan.md` |
| W6 Docs consolidation | 🔶 In progress | T1: Phase 3 evidence recorded; `STATUS.md` owns status |

**Next task:** W1 T1 [HUMAN] (raise Simpro Support cases); W5 T3 (backup script).
**Next decision:** phase order, at end of sprint.

## Simpro access

| Item | Status |
|---|---|
| <ENVIRONMENT_TYPE> API access | Required; awaiting price and access level from Simpro |
| Shared sandbox | Available free via Support case — not yet requested |
| Company IDs (Service, Projects) | Not yet recorded from Simpro setup |

## Open risks

| Risk | Status |
|---|---|
| No off-machine backup | Open — target not yet agreed |
| Knowledge base may not meet metadata/versioning/access requirements | Under audit (W3) |
| Simpro rate limits and token lifetime undocumented | Open — conservative defaults (ADR-010, ADR-012) |
| Backups cover only the Phase 2 pgvector database (`scripts/backup.sh`); Open WebUI's SQLite database (`webui.db`) and uploads are not backed up | Open — W5; target `<home>/clive-backups/` agreed |

## ADRs awaiting a decision

| ADR | Title | Status |
|---|---|---|
| ADR-009 | Phase 3 → Phase 4 handoff (`clive-gateway` as the single Simpro access point) | Decision recorded 2026-10-09 (PR #44). Status line still reads Proposed and its `Related:` line miscites ADR-011; both pending Alex |
| ADR-014 | Simpro data access control model | Proposed. **Conflict for Alex to resolve:** stores `clive_gateway` on the Phase 2 Postgres, against root `CLAUDE.md` §3 |
| ADR-015 | Conversational access approach | Proposed |
