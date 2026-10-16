# CLIVE — Status

> Single source of truth for current status. Update after every completed task
> (`/status-update`). Keep this file short: history belongs in `docs/CHANGELOG.md`,
> decisions in `docs/ADR/`.

**Last updated:** 2026-10-16

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
| W1 Simpro access and sandbox | 🔶 In progress | T2: `docs/simpro/mock-vs-public-api.md` — 16 items: 0 break the client, 4 cosmetic, 9 unknown, 3 match. `Result-*` headers now documented; four unknowns would break the client if they go the wrong way (token request encoding, token invalidation across instances, `/companies/` headers, `ID` in projections) and are the first sandbox checks. T1 [HUMAN] not yet done |
| W2 Doc generation value check | 🔶 In progress | T1 [HUMAN] interviews under way (Alex, 2026-10-16) |
| W3 Knowledge base audit | ⏳ Not started | Bulk ingestion paused until complete |
| W4 Evaluation set | ⏳ Not started | |
| W5 Backups and restore drill | ✅ Complete 2026-10-16 | Closed by Alex with T7 recorded as an accepted risk (Open risks). T1: all data on sdb1; target `<home>/clive-backups/` (sda2). T2: inventory agreed. T3: `scripts/backup.sh` backs up the full inventory except `.env` (GPG key deferred). T4: daily systemd timer at 02:30 installed. T5: `smartd` monitoring both disks; both are past their rated write endurance (recovery plan §9). T6: restore drill passed, about 68 s of commands from checksums to a working Open WebUI (recovery plan §10). T7 (off-machine copy) not done: accepted risk. See `docs/recovery-plan.md` |
| W6 Docs consolidation | ✅ Complete 2026-10-15 | Accepted by Alex. `STATUS.md` owns status; Phase 3 evidence in `phase3/phase3-signoff.md`; ADR index conventions merged; Simpro findings applied to Phase 3B; root `CLAUDE.md` additions merged and `/sprint-task`, `/status-update` confirmed; `PDD-phase3.md` revised and closed; `docs/reviews/` created. Security documentation deferred to Phase 3B Sprint 2 |

**Next task:** W1 T1 [HUMAN] (raise Simpro Support cases); W1 T3 (sandbox contract tests, after Alex reviews T2); W3 T1 (unblocked by W5).
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
| No off-machine backup — accepted until the off-machine copy is in place (Alex, 2026-10-16; no end date set) | Open — W5 closed without T7; target not yet chosen. Cross-disk backups do not cover theft, fire, `rm` or ransomware (`docs/recovery-plan.md` §11) |
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
