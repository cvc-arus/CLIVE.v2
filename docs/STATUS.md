# CLIVE — Status

> Single source of truth for current status. Update after every completed task
> (`/status-update`). Keep this file short: history belongs in `CHANGELOG.md`,
> decisions in `docs/ADR/`.

**Last updated:** 2026-10-12

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | Local AI Platform | ✅ Complete |
| 2 | Production RAG | ✅ Complete (audit in progress — W3) |
| 3 | Simpro API Integration | ✅ Complete — sign-off details to be recorded in W6 task 1 |
| — | Course correction sprint | 🔶 In progress |
| 3B | Simpro Conversational Access | 📝 Planned — PDD drafted; order set at decision point |
| 4 | Document Generation (4A / 4B split pending W2) | ⏳ Not started |
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
| W5 Backups and restore drill | ⏳ Not started | |
| W6 Docs consolidation | ⏳ Not started | |

**Next task:** W6 task 1, then W1 human tasks.
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
| Simpro rate limits and token lifetime undocumented | Open — conservative defaults (ADR-010) |

## ADRs awaiting a decision

ADR-009 (Phase 3 → Phase 4 handoff) is decided in the repo (PR #44); see `docs/ADR/ADR-index.md`.

| ADR | Title | Status |
|---|---|---|
| ADR-014 | Simpro access mechanism (gateway as single access point) | Proposed |
| ADR-015 | Simpro data access control model | Proposed |
| ADR-016 | Conversational access approach | Proposed |
