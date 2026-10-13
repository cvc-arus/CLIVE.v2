# Documentation change list — Phase 3B (Simpro Conversational Access)

**Date:** 2026-10-09
**Basis:** project documents available in this review (`Clive_Scope.txt`,
`CLIVE Enterprise AI Platform` master document, `RevisedScope.txt`,
`Phase3-Sprint1.txt`). The `docs/` folder in the repository was not reviewed
directly, so file names below should be matched to the actual repo files, and
every item should be checked against the codebase (code is the source of truth).

## 1. New documents

| File | Status | Notes |
|---|---|---|
| `docs/PDD-phase3b-simpro-conversational-access.md` | Drafted | Plan, architecture, schema, sprints, schedule, risks |
| `docs/scope/scope-revision-3.md` (or replace `RevisedScope`) | Drafted | Supersedes Revision 2 |
| `docs/ADR/adr-009-phase3-phase4-handoff.md` | Already decided in repo (PR #44) | Repo version is authoritative; add a dated amendment pointing to ADR-014 |
| `docs/ADR/adr-014-simpro-access-mechanism.md` | Drafted (Proposed) | Gateway as the single Simpro access point for all consumers |
| `docs/ADR/adr-014-simpro-access-control-model.md` | Drafted (Proposed) | |
| `docs/ADR/adr-015-conversational-access-approach.md` | Drafted (Proposed) | |
| `docs/user-guide-simpro-qa.md` | Phase 3B Sprint 6 | How to ask questions; what's supported |
| `docs/admin-guide-access-control.md` | Phase 3B Sprint 6 | Adding users, roles, joiner/mover/leaver process |

## 2. Existing documents to update

| Document | Change required | Priority |
|---|---|---|
| Master project document (`CLIVE Enterprise AI Platform`) | §2 Current Status is stale (still describes Phase 1 only). §4/§5: add "Conversational access to Simpro data with role-based restrictions" under Simpro Integration. §15 roadmap: add Phase 3B, note Phase 5 slice pulled forward. | High |
| `Clive_Scope.txt` | Mark as superseded by Scope Revision 3 (keep as historical record). | Low |
| `RevisedScope.txt` (Revision 2) | Mark as superseded; move to historical docs per the living/historical split. | Medium |
| `PDD-phase3.md` | §3 "library-first, service-later" and ADR-003: record that the service is now required (ADR-014). §11/§12 sprint roadmap and milestones: Sprint 6 folded into Phase 3B exit. Already planned for revision. | High |
| Phase 4 PDD | Entry criteria and data source change: consumes `clive-gateway`, not `simpro_client` directly. Add `docgen` service account. | High |
| Phase 5 PDD | Nginx, HTTPS, LAN firewall and Open WebUI hardening delivered in 3B Sprint 2; remaining scope only. | Medium |
| `docs/architecture.md` | Add `clive-gateway`, Simpro tool, Nginx, `clive_gateway` DB; component and data-flow diagrams from the 3B PDD. | High |
| `docs/roadmap.md` | Add Phase 3B and schedule; update Phase 4 start. | High |
| Docker documentation | New `clive-gateway` service (single worker, restart policy, health check, internal network only); new Nginx service. | Medium (with Sprint 2/3) |
| Network documentation | Gateway port internal only; Nginx the only exposed entry point; Open WebUI port no longer published. | Medium (with Sprint 2) |
| Security documentation | Admin-only tool creation; gateway secret handling; chat sharing disabled; access control model; audit log. | High |
| Knowledge base documentation | Rule: Simpro data is never written to PGVector (ADR-016). | Low |
| Backup strategy / `scripts/backup.sh` | Include `clive_gateway` database (roles and audit log). Agree audit retention. | Medium (with Sprint 3) |
| Disaster recovery plan | Gateway is now the single Simpro access point; add restore steps for `clive_gateway`. | Medium |
| Installation guide | New services, `.env` variables (gateway secret, DB credentials), migration step. | Medium (with Sprint 3/5) |
| Development standards | ADR-014 import rule; single-worker constraint; deny-by-default; field classification test. | Medium |
| `.env.example` | Gateway secret, gateway DB URL, gateway URL for the tool. | With Sprint 3 |
| `CHANGELOG.md` | Entry for scope change and new ADRs. | High |
| `structure.txt` | Regenerate after the gateway service is scaffolded. | With Sprint 3 |
| Directory `CLAUDE.md` files | Add the ADR-014 import rule and 3B context so Claude Code sessions follow it. | Medium |

## 3. Inconsistencies found (to resolve against the codebase)

1. **Phase 3 status.** `RevisedScope.txt` shows Sprint 4 (typed client layer)
   in progress with test coverage, regression run and docs outstanding. Later
   project notes indicate the rate limiter and resilience policy (ADR-010) have
   since landed. Confirm the actual state from the code and test run, then set
   the Phase 3 status in Scope Revision 3.
2. **ADR numbering for the rate limiter.** `RevisedScope.txt` §4.2 cites
   "8 req/sec per ADR-005" (from the original PDD's proposed ADR list), while
   the implemented ADRs are ADR-008 (withdrawn as a duplicate) and ADR-010
   (authoritative). Update references to ADR-010.
3. **Original PDD ADR list vs actual ADRs.** `PDD-phase3.md` proposed ADR-001 to
   ADR-005 with different subjects from the ADRs actually written (001–013).
   Align the PDD's ADR table with the real ADR index.
4. **Phase 4 data source.** The master document and Revision 2 state Phase 4
   "consumes `simpro_client` directly as a Python library". This now conflicts
   with ADR-014 and must be changed everywhere it appears.
5. **pydantic-settings versions.** `simpro_client` pins 2.14.2 and `simpro_mock`
   2.15.0. Not a defect, but worth aligning when the gateway adds a third consumer.
6. **Obsolete planning prompt.** `Phase3-Sprint1.txt` contains a Sprint 2
   kick-off prompt for a mock API on the shared PGVector container, which was
   not what was built (`simpro-mock-db` is a separate container on port 5433).
   Keep as a historical transcript only.

## 4. Suggested order of updates

1. Resolve inconsistency 1 (Phase 3 status) — it affects every status table.
2. Check ADR-009 (decided in PR #44), then commit ADR-014, ADR-015, ADR-016 and Scope Revision 3.
3. Update the master document, `PDD-phase3.md`, Phase 4 PDD, roadmap and CHANGELOG.
4. Update architecture, security and development standards.
5. Leave Docker, network, installation, backup and `.env.example` updates to the
   sprints that introduce those changes, as usual.
