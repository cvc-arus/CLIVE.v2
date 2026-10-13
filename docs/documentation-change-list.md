# Documentation change list — Phase 3B (Simpro Conversational Access)

**Date:** 2026-10-09 · **Reconciled with the repository:** 2026-10-13 (commit `064b596`)
**Basis:** drafted from the project documents available in a planning session
without repository access (`Clive_Scope.txt`, the master project document,
`RevisedScope.txt`, `Phase3-Sprint1.txt`). On 2026-10-13 every item was checked
against the repository: file names now use real repo paths, items already done
are marked, and documents that do not exist are marked "to create".

## 1. New documents

| File | Status | Notes |
|---|---|---|
| `docs/PDDs/PDD-phase3b-simpro-conversational-access.md` | Drafted | Plan, architecture, schema, sprints, schedule, risks |
| `docs/scope/scope-rev3.md` | Drafted (historical) | Supersedes Revision 2 (`docs/scope/scope-rev2.md`) |
| `docs/ADR/adr-009-phase3-phase4-handoff.md` | Exists; decision recorded 2026-10-09 (PR #44) | Repo version is authoritative and already makes `clive-gateway` the single Simpro access point for every consumer. No new ADR needed for that. Its Status line (still Proposed) and its `Related:` line (cites ADR-011 for access control) are pending Alex |
| `docs/ADR/adr-014-simpro-access-control-model.md` | Drafted (Proposed) | |
| `docs/ADR/adr-015-conversational-access-approach.md` | Drafted (Proposed) | |
| `docs/user-guide-simpro-qa.md` | Phase 3B Sprint 6 (to create) | How to ask questions; what's supported |
| `docs/admin-guide-access-control.md` | Phase 3B Sprint 6 (to create) | Adding users, roles, joiner/mover/leaver process |

## 2. Existing documents to update

| Document | Change required | Priority |
|---|---|---|
| `docs/scope/master-project-document.md` | **Historical** (`docs/README.md` §6), so not rewritten. Its stale §2 "Current Status" is superseded by `docs/roadmap.md` / `docs/STATUS.md`. Conversational access and Phase 3B go into the living documents (`docs/roadmap.md`, `docs/architecture.md`) instead | — |
| `docs/scope/clive-scope.md` (was `Clive_Scope.txt`) | Already historical (`docs/README.md` §6). **Done** | — |
| `docs/scope/scope-rev2.md` (was `RevisedScope.txt`) | Already historical, "superseded by `roadmap.md`" (`docs/README.md` §6). **Done** | — |
| `docs/PDDs/PDD-phase3.md` | As-built at 2026-09-04 (§1–§8). §4/§5/§7/§8 still say the handoff ADR is "not yet written"; record ADR-009's decision (gateway). Revision already marked "To do: revise now" in `docs/README.md` §5 | High |
| `docs/PDDs/PDD-phase4.md` | Entry criteria and data source change: consumes `clive-gateway` (ADR-009), not `simpro_client` directly; §2/§4 still describe the handoff as open. Add `docgen` service account | High |
| Phase 5 PDD | Does not exist (only `PDD-phase1`–`4`). To create when Phase 5 is scoped, listing only the scope left after 3B Sprint 2 | Medium |
| `docs/architecture.md` | Add `clive-gateway`, Simpro tool, Nginx, `clive_gateway` DB **as Planned**; component and data-flow diagrams from the 3B PDD | High |
| `docs/roadmap.md` | Add Phase 3B and schedule; update Phase 4 start. Status column becomes a link to `docs/STATUS.md` when W6 transfers ownership | High |
| Docker documentation | No separate document; ports, volumes and containers live in `docs/architecture.md`. New `clive-gateway` and Nginx services go there | Medium (with Sprint 2/3) |
| Network documentation | No separate document; use `docs/architecture.md`. Gateway port internal only; Nginx the only exposed entry point | Medium (with Sprint 2) |
| Security documentation | Does not exist; to create (admin-only tool creation, gateway secret handling, chat sharing disabled, access control model, audit log) | High |
| Knowledge base documentation | No separate document (nearest: `docs/PDDs/PDD-phase2.md`). Rule: Simpro data is never written to PGVector (ADR-015) | Low |
| Backup strategy / `scripts/backup.sh` | Strategy is described in `docs/installation.md` §9 and `docs/PDDs/PDD-phase2.md` §8. `scripts/backup.sh` dumps only the Phase 2 pgvector database. Include `clive_gateway`; agree audit retention | Medium (with Sprint 3; W5 first) |
| Disaster recovery plan | Does not exist; created by W5 | Medium |
| `docs/installation.md` | New services, `.env` variables (gateway secret, DB credentials), migration step | Medium (with Sprint 3/5) |
| `docs/development-standards.md` | ADR-009 import rule; single-worker constraint; deny-by-default; field classification test | Medium |
| `.env.example` | Gateway secret, gateway DB URL, gateway URL for the tool | With Sprint 3 |
| `docs/CHANGELOG.md` | Entry for scope change and new ADRs | High |
| `structure.txt` | Generated; regenerate with the command in `docs/README.md` after files are added | With each sprint |
| Directory `CLAUDE.md` files | ADR-009 import rule: **done** in root `CLAUDE.md` §3 (PR #45). Add 3B context when Phase 3B starts | Medium |

## 3. Inconsistencies found (resolved against the codebase, 2026-10-13)

1. **Phase 3 status.** Resolved: Phase 3 closed 2026-10-09 (`docs/roadmap.md`,
   `docs/CHANGELOG.md` entry of 2026-10-12). `uv run pytest -q` at `064b596`:
   240 passed, 1 skipped (mock running).
2. **ADR numbering for the rate limiter.** No living document cites ADR-005 for
   the rate limiter (`roadmap.md` fixed 2026-10-02, see `docs/doc-audit.md`).
   Remaining mentions are in historical documents only
   (`docs/scope/scope-rev2.md`, `docs/phase3/sprints/phase3-sprint4-contract.md`);
   those get a dated correction note only if Alex asks.
3. **Original PDD ADR list vs actual ADRs.** Not found: the current
   `PDD-phase3.md` is an as-built rewrite with no ADR table. The real issue is
   its stale handoff text (see §2).
4. **Phase 4 data source.** Living documents already say Phase 4 consumes the
   gateway (`docs/roadmap.md`, root `CLAUDE.md`). Still stale:
   `docs/PDDs/PDD-phase4.md`. The master document and Revision 2 are historical.
5. **pydantic-settings versions.** Confirmed: `simpro_client` pins 2.14.2 and
   `simpro_mock` 2.15.0. Not a defect, but worth aligning when the gateway adds
   a third consumer.
6. **Obsolete planning prompt.** `Phase3-Sprint1.txt` is not in the repository
   or on the host; unverifiable. What was built is confirmed: `simpro-mock-db`
   is a separate container on port 5433.

## 4. Suggested order of updates

1. Phase 3 status: resolved (inconsistency 1).
2. Alex updates ADR-009's Status and `Related:` lines; commit ADR-014, ADR-015 and Scope Revision 3.
3. Update `PDD-phase3.md`, `PDD-phase4.md`, roadmap and CHANGELOG.
4. Update architecture, security and development standards.
5. Leave Docker, network, installation, backup and `.env.example` updates to the
   sprints that introduce those changes, as usual.
