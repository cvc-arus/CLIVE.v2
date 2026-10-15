# CLIVE — Status

> Single source of truth for current status. Update after every completed task
> (`/status-update`). Keep this file short: history belongs in `docs/CHANGELOG.md`,
> decisions in `docs/ADR/`.

**Last updated:** 2026-10-15

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
| W5 Backups and restore drill | 🔶 In progress | T1: all data on sdb1; target `<home>/clive-backups/` (sda2). T2: inventory agreed. T3: `scripts/backup.sh` backs up the full inventory except `.env` (GPG key deferred). T4: daily systemd timer at 02:30 installed. T5: `smartd` monitoring both disks; both are past their rated write endurance (recovery plan §9). T6: restore drill passed, about 68 s of commands from checksums to a working Open WebUI (recovery plan §10). T7 (off-machine copy) to be done later. See `docs/recovery-plan.md` |
| W6 Docs consolidation | 🔶 In progress | T1: Phase 3 evidence recorded; `STATUS.md` owns status. T2: Scope Revision 3 recorded as historical. T3: ADR index conventions merged; ADR-014 and ADR-015 indexed as Proposed. T4: Simpro findings applied to the Phase 3B PDD and ADR-014. T5: Phase 3B and the gateway added to the roadmap; Phase 4 PDD and `architecture.md` §6 follow ADR-009. T6: root `CLAUDE.md` additions merged; short sprint template allowed; package documents indexed. Alex to confirm `/sprint-task` and `/status-update` appear after a restart. T7: High change-list items done except security documentation, deferred to Phase 3B Sprint 2 |

**Next task:** W1 T1 [HUMAN] (raise Simpro Support cases); W6 acceptance review (Alex); W5 T7 [HUMAN] (off-machine copy) later.
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
| No off-machine backup | Open — agreed, to be done later (Alex, 2026-10-14); target not yet chosen |
| Both SSDs are past their rated write endurance (129 % and 116 %), from the same batch, so both could fail close together | Open — replace both, `sdb` first; firmware update to be looked into (Alex, 2026-10-14). See `docs/recovery-plan.md` §9 |
| Knowledge base may not meet metadata/versioning/access requirements | Under audit (W3) |
| Simpro rate limits and token lifetime undocumented | Open — conservative defaults (ADR-010, ADR-012) |
| `.env` is not backed up until the GPG key pair exists | Open — GPG key deferred (Alex, 2026-10-14) |
| Open WebUI's signing key (`WEBUI_SECRET_KEY`) is generated inside the container, not backed up: a restore or container rebuild logs everyone out | Open — fix needs `WEBUI_SECRET_KEY` in `.env` and Compose (live change, not decided). See `docs/recovery-plan.md` §10 |

## ADRs awaiting a decision

| ADR | Title | Status |
|---|---|---|
| ADR-014 | Simpro data access control model | Proposed. Storage conflict with root `CLAUDE.md` §3 resolved by Alex 2026-10-15 (narrow exception in §3) |
| ADR-015 | Conversational access approach | Proposed |
