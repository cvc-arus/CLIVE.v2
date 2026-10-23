# CLIVE Documentation Index

> **Status: adopted 2026-09-29.** Structure agreed by Alex. Section 6 actions
> are done (2026-10-05; `phase3-summary.md` stays historical, Alex 2026-10-15); section 7
> actions are still to do; section 8 records the decisions made.

This index lists every document, what it is for, and whether it is kept up
to date. If a document is not listed here, either add it here or delete it.

## 1. Document types

| Type | Meaning | Rule |
|---|---|---|
| **Living** | Describes the system as it is now | Must match the code. Updated whenever the code it describes changes. |
| **Reference** | Generated from code or configuration | Regenerate it rather than hand-edit it. |
| **Decision** | ADRs and PDDs | ADR decisions are never rewritten; supersede them with a new ADR. PDDs are revised at phase sign-off. |
| **Historical** | A record of a sprint, audit or plan at a point in time | Never rewritten to match later code. Factual errors get a dated correction note at the end. |

## 2. Rules for all documents

- **One fact, one home.** Each fact is owned by exactly one living document
  (see the "Owns" column). Other documents link to it instead of repeating it.
- **Status lives only in `STATUS.md`.** Phase, sprint and workstream status,
  Simpro access, open risks and ADRs awaiting a decision are stated there and
  nowhere else (since 2026-10-13). Other documents link to it.
- **No volatile numbers in living documents.** Test counts, lint error
  counts and commit hashes go stale. Give the command to run instead.
  Historical documents may record numbers, with the commit they came from.
- **Planned is not implemented.** Anything not in the code is labelled
  *Planned* or *Proposed* with a pointer to where it is planned.
- **No build or host facts in tracked files (ADR-017).** They live in the
  untracked `simpro/private/` (contents listed in
  `simpro/private-notes.template.md`) or in `.env`. Before every commit,
  `python3 scripts/check-public-safe.py` must exit 0.
- **Commit hashes before the public release.** The repository's history was
  rewritten for publication (2026-10-20, public-release T10), so hashes cited in
  documents written before then refer to the old private repository's history.
  The old-to-new commit map is in the private store.
- Evidence and style rules for editing are in `docs/CLAUDE.md`.

## 3. Living documents

| Document | Owns | Current state (re-verify before relying on this) |
|---|---|---|
| `../README.md` | Project overview, links into `docs/` | Rewritten 2026-10-05 as the project overview (purpose, modules, architecture, services, documentation map); status, tree and install steps are links to their owners. 2026-10-06: services table marks every port localhost-only; licence sentence removed. 2026-10-13: status pointers name `docs/STATUS.md`; `roadmap.md` is linked for phases and scope. 2026-10-19: Ownership names the proprietary `LICENSE`. 2026-10-21: clone command points at the new repository `CLIVE.v2` (public-release T10) |
| `STATUS.md` | Current status: phases, current sprint and workstreams, Simpro access, open risks, ADRs awaiting a decision (the only place status is stated) | Added 2026-10-13 with the course correction package (PR #49). 2026-10-13: became the sole owner of status (W6 T1); Phase 3 row links to `phase3/phase3-signoff.md`. 2026-10-16: W5 complete; no off-machine backup recorded as an accepted risk. 2026-10-17: live Simpro access recorded (Simpro access table, W1 row); write-access risk added. 2026-10-17: live smoke check results (W1 row, Simpro access). 2026-10-17: W1 T3 and T4 (two of three) recorded; next task names the held `ID` item. 2026-10-17: ADR-016 added to ADRs awaiting a decision. 2026-10-17: Simpro access row — listing `/companies/` allowed, no requests to other companies (Alex). 2026-10-19: ADR-016 accepted (removed from ADRs awaiting a decision). 2026-10-19: W1 T3/T4 merged (PRs #86, #87); next task W1 T5. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017). 2026-10-19: public-release row records ADR-017's acceptance, the T7 decision and T9. 2026-10-21: public-release T8–T12 and T14 done (public repository `CLIVE.v2`); next task T13. 2026-10-21: public-release complete, course correction resumed, four open risks deferred until production (Alex). 2026-10-21: W3 T1 recorded. 2026-10-23: W3 T2 recorded. 2026-10-23: ADR-018 added to ADRs awaiting a decision, then accepted (removed). 2026-10-23: W3 row notes the Open WebUI 0.12.3 upgrade |
| `simpro/simpro-api-findings.md` | What Simpro has told CVC about its API (registration, access scoping, sandbox, rate limits, custom fields), what is still unverified, and the implications for CLIVE | Added 2026-10-12 with the course correction package; recorded in this index 2026-10-14 (W6 T6). §2 applied to the Phase 3B PDD and ADR-014 (W6 T4). 2026-10-17: Alex's answers after live access (sandbox not used, company IDs recorded, application permissions, Support cases not needed); §6 maps the delivered credentials to `.env` variables. 2026-10-17: smoke check run; only the two configured companies; customers and sites build-wide; token encoding settled. 2026-10-17: §2.1 documents the opt-in live contract tests and how to run them (W1 T3). 2026-10-17: §2.3 — listing `/companies/` allowed, no requests to other companies (Alex). 2026-10-19: CVC-specific values moved to the private build notes (ADR-017) |
| `simpro/mock-vs-public-api.md` | How the mock and `simpro_client` compare with Simpro's public documentation on what the published spec cannot settle (`columns` and `ID`, pagination headers, `limit`, `/companies/` paging, error responses, token handling), with a severity per item | Added 2026-10-16 (W1 T2) from the full published spec's documentation text; the portal returns 403 here. 2026-10-17: §6 live results — 3 break the client (items 1, 4, 17), 6 cosmetic, 6 unknown, 4 match. 2026-10-17: §5 marked superseded by §6.2. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017) |
| `simpro/private-notes.template.md` | What the untracked private store `docs/simpro/private/` must contain (build and host facts kept out of tracked files, ADR-017) and how to restore it | Added 2026-10-19 (public-release sprint T2). 2026-10-19: lists the W2 and W3 private files (T7) |
| `reviews/README.md` | Rules for `docs/reviews/` (naming, historical header, where findings go) and the reviews planned there | Added 2026-10-15 (Alex). Each review in the folder is historical and listed in §6. 2026-10-19: reviews are public; client figures and names go to the private store (ADR-017, public-release T7) |
| `templates/sprint-full.md`, `templates/sprint-short.md` | Sprint plan formats: full (14 sections) for sprints that change infrastructure, security or data, short otherwise (root `CLAUDE.md` §5, `development-standards.md` §8) | Added 2026-10-13 with the course correction package; recorded in this index 2026-10-14 (W6 T6) |
| `roadmap.md` | Phase list and phase scope (status is in `STATUS.md`) | Fixed 2026-10-02 (`doc-audit.md`): Phase 3 typed layer shown as implemented; remaining work is ADR-009 and sign-off. 2026-10-05: Phase 4 handoff mechanism now deferred to ADR-009. 2026-10-08: "Phase 3 — Remaining Work" records ADR-013 as implemented, names `test_spec_conformance.py` and the two integration modules, and adds a defect-triage item pointing at `known-issues.md`. 2026-10-08: that item no longer lists the two mock query defects, which were fixed. 2026-10-12: Phase 3 marked closed 2026-10-09, Phase 4 no longer blocked, "Remaining Work" replaced by a close-out section, and the Phase 4 entry criteria and planned-scope rows updated for ADR-009's decision. 2026-10-13: Status column replaced by a link to `STATUS.md`, which now owns status (course correction W6 T1); the Phase 4 note no longer states status. 2026-10-15: Phase 3 close-out says the lint debt was cleared (PR #47). 2026-10-14: Phase 3B row and "Phase 3B Planned Scope" section added; Phase 5 notes the minimum slice planned in 3B; order relative to Phase 4 points at `STATUS.md` (W6 T5). 2026-10-17: Phase 3 note and close-out say live access arrived 2026-10-16 (read-only). 2026-10-17: Phase 3 close-out says the live smoke check settled three of the four unverifiable behaviours |
| `architecture.md` | Services, ports, containers, `simpro_client` and `simpro_mock` design | Fixed 2026-10-02 (`doc-audit.md`): typed layer, rate limiter, exception hierarchy and response handling match `client.py`. 2026-10-05: port table (all `127.0.0.1`), volumes, mock DB `.env` keys and healthchecks match `docker-compose.yml`. 2026-10-06: mock base image tag matches `services/simpro_mock/Dockerfile`. 2026-10-06: response handling updated for transient-error retries (ADR-010 §2.2); `auth.py` token requests go through the rate limiter; `SimproAuthRefreshError` added. 2026-10-06: `SimproAuthError` context fields (ADR-011); ADR-011 accepted. 2026-10-06: `config.py` row covers per-`auth_mode` validation; `company_id_service` / `company_id_projects` marked reserved. 2026-10-06: header says maintained since 2026-09-04. 2026-10-06: response handling records the `SIMPRO_MAX_RETRY_DELAY` cap on `Retry-After` (ADR-012). 2026-10-07: `auth.py` row and the `401` row record the refresh lock and token-aware invalidate (ADR-012 §2.2). 2026-10-07: §5.2 route count, §5.3 data model and §5.4 endpoint table updated for the ADR-013 S2 route corrections (Projects removed, attachments and status codes re-pathed). 2026-10-08: §5.1–§5.5 rewritten for the completed ADR-013 re-shape and re-verified against the code — module layout, 16 ORM classes / 17 tables, the 25-route surface with the three polymorphic customer routes, the dropped `projects` table, the `serializers.py` / `projection.py` layers, per-model filter maps and the 400 on an unknown filter. Counts in §5.1 and §5.2 were taken by importing the packages on 2026-10-08. 2026-10-08: §5.4 gained an Ordering paragraph for the new `ordering.py` (`orderby`, the 400 on an unorderable field, the `id` ordering that pagination needs, and `limit`). 2026-10-13: intro points at `STATUS.md` for phase status (W6 T1). 2026-10-14: §6 records ADR-009's decision (`clive-gateway`, not built yet) instead of describing the handoff as open (W6 T5). 2026-10-14: §6.1 lists the Phase 3B components (`clive-gateway`, `clive_gateway` DB, Simpro tool, `nginx`) and request path, all marked Planned (W6 T7). 2026-10-15: `clive_gateway` row records Alex's narrow §3 exception (ADR-014). 2026-10-17: mock pagination notes that `/companies/` is unpaginated (W1 T4). 2026-10-17: `columns` paragraph — mock adds no `ID`, client adds required fields (ADR-016). 2026-10-19: ADR-016 accepted 2026-10-23: image tags for `open-webui` and `ollama` pinned (ADR-018) |
| `installation.md` | Setting up and running the stack | Fixed 2026-10-02 (`doc-audit.md`). Docker steps not re-run. 2026-10-05: `SIMPRO_MOCK_DB_*` keys and localhost-only ports added. 2026-10-06: prerequisites name `uv` only; diagnostic run with `uv run`; mock started with `--build` 2026-10-14: §9 Backups rewritten for the extended `scripts/backup.sh` (W5 T3). 2026-10-14: §9 daily systemd timer setup added (W5 T4). 2026-10-14: §9 disk health (`smartd`) setup added (W5 T5). 2026-10-14: §9 links the restore procedure (W5 T6).. 2026-10-19: §9 installs the backup unit and smartd configuration from templates (`sed` render, `smartd.conf.local`; ADR-017). 2026-10-21: §2 clones the new repository `CLIVE.v2` into `CLIVE-I` (public-release T10) |
| `development-standards.md` | Coding, tooling, Git, sprint template | Fixed 2026-10-02 (`doc-audit.md`). 2026-10-06: branch-naming convention added (§7); §2 run commands corrected to `uv run`. 2026-10-06: `client.py` docstring remark removed (§1); feature branches merge to `develop` (§7). 2026-10-15: §2 says both whole-repo lint checks pass. 2026-10-14: §8 allows the short sprint template for sprints that do not change infrastructure, security or data (W6 T6) |
| `testing.md` | Test layers, markers, how to run them | Fixed 2026-10-02 (`doc-audit.md`): all test modules listed, no counts. 2026-10-06: `test_retries.py` row covers transient-error retries; `test_auth.py` row covers limiter use; `test_retries.py` row covers refresh failure. 2026-10-06: auth-error context in `test_auth.py` / `test_retries.py` rows. 2026-10-06: mock-start and diagnostic commands corrected (`--build`, `uv run`). 2026-10-06: `test_config.py` row covers `auth_mode` validation. 2026-10-06: diagnostic script line count removed; `test_auth.py` / `test_retries.py` rows list every test. 2026-10-07: §1 gained a `test_spec_conformance.py` row and §3 now covers both integration modules, including `test_client_mock_drift.py` (ADR-013). 2026-10-07: §4 resource count corrected to 11 served resources. 2026-10-08: §1, §3 and §4 updated for ADR-013 S3–S6 — `test_spec_conformance.py` records the empty baseline, `test_models.py`/`test_endpoints.py`/`test_route_contract.py` rows cover their new assertions, §3 lists the S6 query-handling and drift tests, and §4's resource count became a route count. 2026-10-08: §3's `test_simpro_mock_v2.py` row lists the six new `orderby` / `limit` / page-determinism tests. 2026-10-15: lint paragraph says both whole-repo checks pass. 2026-10-17: `test_simpro_mock_v2.py` covers `/companies/` being unpaginated (W1 T4). 2026-10-17: offline intro and §3 cover the opt-in `live` marker and `test_live_contract.py`; `test_pagination.py` and `test_models.py` rows cover `/companies/` and empty dates (W1 T3, T4). 2026-10-17: projection tests described for ADR-016. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017) |
| `recovery-plan.md` | Recovery plan: data location per disk, backup target, backup inventory and procedure, restore procedure and drill reports | Added 2026-10-14 (course correction W5 T1): disk layout, live data per disk, the six unmounted `/data` directories, and the backup target `~/clive-backups/`; later sections are placeholders for W5 T2–T7. 2026-10-14: §7 backup inventory added (W5 T2); §6 records the `postgres:16-alpine` archiving decision 2026-10-14: §8 backup procedure and first-run evidence added (W5 T3); §7 marks `.env` as deferred. 2026-10-14: §8 records whitespace stripping in `.env` loading and the run with `.env` settings. 2026-10-14: §8 schedule (systemd timer) and its first run added (W5 T4). 2026-10-14: §9 disk health baseline and the endurance finding added (W5 T5). 2026-10-14: §10 restore drill and full-rebuild procedures and the drill report added (W5 T6). 2026-10-16: §11 records the off-machine copy as an accepted risk (W5 closed).. 2026-10-19: §7 item 8, the private build notes (ADR-017). 2026-10-19: home paths, the GPG example email and the drill container address replaced with placeholders (ADR-017) 2026-10-23: §7 item 7 records the pinned image tags (ADR-018) and the upgrade to 0.12.3 |
| `known-issues.md` | Open discrepancies and defects | Fixed 2026-10-02 (`doc-audit.md`): stale Sprint 4 entry removed; unused mock settings and lint debt added. 2026-10-05: date removed from title (each entry keeps its own). 2026-10-08: added the cutover-claim entry, marked RESOLVED by ADR-013, with the two caveats that remain unverifiable without live access; the preamble now says resolved entries are marked rather than deleted. 2026-10-08: added two entries — the mock accepts and ignores `orderby` and `limit`, and collection routes paginate without an `ORDER BY` — then marked both RESOLVED the same day when they were fixed, carrying forward one caveat (`limit`'s upstream semantics are unverified). 2026-10-08: the unused mock settings entry marked RESOLVED when the two fields were removed. 2026-10-15: lint debt entry marked RESOLVED (cleared by PR #47 on 2026-10-12). 2026-10-17: three open entries from the live smoke check (`/companies/` paging, `ID` in projections, empty date strings). 2026-10-17: resolved cutover entry notes which caveats the live check settled. 2026-10-17: `/companies/` paging entry marked RESOLVED (W1 T4). 2026-10-17: empty-date entry marked RESOLVED (W1 T4). 2026-10-17: `ID`-in-projections entry marked RESOLVED under ADR-016 (Proposed). 2026-10-19: ADR-016 accepted |
| `CHANGELOG.md` | What changed, per sprint | Fixed 2026-10-02 (`doc-audit.md`): Sprint 4 entry added. 2026-10-05: shallow-history caveat removed from intro. 2026-10-06: entries added for the compose hardening, `verify.sh`, deterministic seed and mock `Dockerfile` changes. 2026-10-06: entry added for the ADR-012 retry delay ceiling. 2026-10-07: entry added for the `AuthManager` refresh lock. 2026-10-07: entries added for ADR-013 (drafted, then accepted), the vendored Simpro contract and the two new test modules, and for the S2 route corrections. 2026-10-08: entries added for ADR-013 S3–S7 — the three re-shape waves, the mock's `columns` projection and loud filtering, and the documentation close-out, and for the post-close-out corrections to `CLAUDE.md` §4, this file and `roadmap.md`. 2026-10-08: entry added for the mock's `orderby` / `limit` implementation and its now-deterministic pagination. 2026-10-12: entries added for ADR-009's decision and for closing Phase 3. 2026-10-13: entry added for the course correction sprint start and `STATUS.md` taking over status. 2026-10-14 to 2026-10-17: entries for W5 backups, W6 close, W1 T2 comparison, live access and the live smoke check (this cell caught up 2026-10-17). 2026-10-17: entries for the doc clean-up, W1 T4 (two fixes) and W1 T3. 2026-10-17: entries for ADR-016, the ADR-014 update and the company rule. 2026-10-19: entries for accepting ADR-016 and merging W1 T3/T4. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017). 2026-10-19: entry for accepting ADR-017. 2026-10-21: entries for public-release T8–T12 and T14, and for the sprint's close. 2026-10-21: entry for W3 T1. 2026-10-23: entry for W3 T2. 2026-10-23: entries for proposing and accepting ADR-018, and for the Open WebUI upgrade |

## 4. Reference documents (regenerate, don't hand-edit)

| Document | Generated from |
|---|---|
| `simpro-mock-api-reference.md` | `services/simpro_mock/simpro_mock/routers.py`, `schemas.py`, `serializers.py`, `filtering.py`, `projection.py`, `middleware.py`. Routes **and** field sets are spec-derived (ADR-013), with the conformance baseline empty as of S5; §4 covers the S6 `columns` projection and per-resource filter maps |
| `contracts/simpro-openapi-v1-get-subset.json` | Simpro's published OpenAPI 2.0 spec, pruned to the GET operations CLIVE reads. Regenerate with `uv run python scripts/prune-simpro-spec.py <full-spec.json> docs/contracts/simpro-openapi-v1-get-subset.json`. Normative for model field names, types and optionality (ADR-013); enforced by `tests/test_spec_conformance.py` |
| `../services/simpro_mock/configuration.md` | `services/simpro_mock/simpro_mock/config.py` |
| `../structure.txt` | Tracked files only. Regenerate from the repo root after adding, moving or deleting files (needs `tree` ≥ 2.0): |

```bash
{ echo "# Generated from 'git ls-files'. Do not edit by hand; regenerate with the command in docs/README.md."; git ls-files | grep -vE '__pycache__|\.egg-info/' | tree --fromfile . --charset=utf-8 -a; } > structure.txt
```

## 5. Decision documents

| Document | Notes |
|---|---|
| `ADR/ADR-index.md` | Owns ADR status. Must list every ADR. |
| `ADR/adr-001-local-llm-stack.md` | Phase 1. 2026-10-23: image tags superseded by ADR-018 |
| `ADR/adr-002-vector-database-pgvector.md` | Phase 2 |
| `ADR/adr-003-document-extraction-tika.md` | Phase 2 |
| `ADR/adr-004-http-client-choice.md` | Phase 3 |
| `ADR/adr-005-auth-strategy.md` | Phase 3 |
| `ADR/adr-006-library-first-architecture.md` | Phase 3 |
| `ADR/adr-007-configuration-management.md` | Phase 3 |
| `ADR/adr-009-phase3-phase4-handoff.md` | Decision recorded 2026-10-09 (Alex): Option B, a single `clive-gateway` service imports `simpro_client` and serves every other consumer over HTTP. Accepted (Status line updated by Alex 2026-10-15); partially supersedes ADR-006's "no service wrapper" |
| `ADR/adr-010-resilience-policy.md` | Accepted, implemented with deviations (see `../src/simpro_client/CLAUDE.md`); §2.5 superseded by ADR-011 |
| `ADR/adr-011-exception-hierarchy-and-auth-errors.md` | Accepted 2026-10-06, implemented (supersedes ADR-010 §2.5) |
| `ADR/adr-012-retry-delay-ceiling-and-auth-concurrency.md` | Accepted 2026-10-06 (supersedes ADR-010 §2.3, extends §2.1) |
| `ADR/adr-013-reshape-to-published-simpro-spec.md` | Accepted 2026-10-07, implemented 2026-10-08 (all 7 sprints). Governs field names, types and optionality via `contracts/simpro-openapi-v1-get-subset.json`; supersedes `adr-mock-simpro-api.md` "Capabilities & Coverage". "`ID` is always included" in §5 superseded by ADR-016 (2026-10-19) |
| `ADR/adr-014-simpro-access-control-model.md` | Proposed 2026-10-09 (Phase 3B). Stores `clive_gateway` on the Phase 2 Postgres; the conflict with root `CLAUDE.md` §3 was resolved by Alex on 2026-10-15 with a narrow exception in §3. 2026-10-17: "Revisit if" says live read-only checks instead of sandbox testing. 2026-10-17: updated for live access — no dedicated read-only security group (so the gateway is the only boundary), only the two configured companies, customers and sites build-wide so company scope cannot restrict them; "Revisit if" reworded; still Proposed. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017) |
| `ADR/adr-015-conversational-access-approach.md` | Proposed 2026-10-09 (Phase 3B): tool calling over a fixed query catalogue |
| `ADR/adr-016-columns-projection-required-fields.md` | Accepted 2026-10-19 (Alex): the mock adds nothing to a `columns` projection, and the client adds the model's missing required fields; supersedes "`ID` is always included" in ADR-013 §5 |
| `ADR/adr-017-public-repository-private-build-facts.md` | Proposed 2026-10-19, **accepted** 2026-10-19 (Alex): build and host facts move to an untracked private store; a guard script checks tracked files and history; the rewritten history is published to a new repository |
| `ADR/adr-018-pin-container-images-to-release-tags.md` | Proposed 2026-10-23, **accepted** 2026-10-23 (Alex): every image in `docker-compose.yml` by exact release tag (`open-webui` `v0.12.3`, `ollama` `0.31.2`); upgrades are deliberate PRs after release notes and a backup; supersedes ADR-001's image tags |
| `ADR/adr-mock-simpro-api.md` | Decision stands; its "Capabilities & Coverage" list is superseded by ADR-013 |
| `ADR/adr-008-rate-limiting-strategy.md` | Withdrawn 2026-09-29 (duplicate of ADR-010). Kept for history |
| `PDDs/PDD-phase1.md`, `PDD-phase2.md` | Phases complete. 2026-10-14: `PDD-phase2.md` §8 has a dated note that the Phase 2 backup script was replaced in course correction W5. 2026-10-19: `PDD-phase2.md` home paths replaced (ADR-017) |
| `PDDs/PDD-phase3.md` | **Closed.** Revised as-built and closed 2026-10-15 at commit `864264b` (Alex): typed layer, ADR-013 contract, ADR-009 handoff, plan vs delivery, items carried forward. Not maintained; current architecture is in `architecture.md`. (Earlier: as-built 2026-09-04; 2026-10-14 handoff lines updated in W6 T3) |
| `PDDs/PDD-phase3b-simpro-conversational-access.md` | Draft 0.1 (2026-10-09), awaiting approval. Phase 3B plan: `clive-gateway`, access control, query catalogue, minimum security slice. 2026-10-14: Simpro findings applied (W6 T4). 2026-10-15: ADR-014 storage conflict note marked resolved. 2026-10-17: Testing row uses opt-in read-only live contract tests instead of the sandbox. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017) |
| `course-correction-plan.md` | Course correction plan v2 (2026-10-12), approved. Task files in `sprints/course-correction/`. 2026-10-17: amendment of 2026-10-16 (Alex) — live read-only access instead of the sandbox; decision-point scenarios and open items updated. 2026-10-19: CVC build and host values replaced with variable names, placeholders or links to the private build notes (ADR-017) |
| `PDDs/PDD-phase4.md` | Draft. Handoff link fixed 2026-10-02 (now ADR-009). 2026-10-14: §1–§6 and the diagram consume Simpro through `clive-gateway` (ADR-009) instead of importing `simpro_client`; entry criteria add the gateway's query catalogue (W6 T5). 2026-10-14: §3 adds the `docgen` service account (W6 T7) |

## 6. Historical documents

Phase 3 documents use a `phase3-` prefix. Sprint records move into
`docs/phase3/sprints/`, keeping the prefixed names, so they are visibly
separate from living documents. Each gets a one-line header:
`> Historical record as of <date>, commit <hash>. Not maintained.`

| Current path | Action / status |
|---|---|
| `phase1/summary.md` | Keep as historical. Done 2026-10-05: correction note added (container is `clive-ollama`; original commands unchanged) |
| `phase2/summary.md` | Keep as historical |
| `phase3/phase3-summary.md` | Keep as the Phase 3 historical summary. Decided 2026-10-15 (Alex): it stays a historical record and is not merged into `architecture.md` / `testing.md` |
| `phase3/phase3-signoff.md` | Historical. Phase 3 sign-off evidence (close, test run at commit `8b11657`, items carried past the close), added 2026-10-13 (W6 T1) |
| `phase3/sprints/phase3-sprint4-contract.md` | Done 2026-10-05: moved to `phase3/sprints/`. Still the reference spec for Sprint 4 |
| `phase3/sprints/phase3-sprint4-preflight-audit.md` | Done 2026-10-05: moved to `phase3/sprints/` |
| `phase3/sprints/phase3-sprint4-architecture-summary.md` | Done 2026-10-05: moved to `phase3/sprints/` (baseline snapshot) |
| `phase3/sprints/phase3-sprint4-2-typed-python-sdk-endpoint-layer.md` | Done 2026-10-05: moved to `phase3/sprints/`, renamed (lowercase `sdk`), correction note added (claims don't match the repository) |
| `phase3/sprints/phase3-sprint4-4-pagination-and-retries.md` | Done 2026-10-05: moved to `phase3/sprints/` |
| `phase3/sprints/phase3-sprint4.md` | Done 2026-10-05: moved to `phase3/sprints/` and kept as historical (not deleted). Chat fragment duplicating the contract's test sequence |
| `doc-audit.md` | Keep as historical. Full `/doc-check all` report of 2026-10-01, with a 2026-10-02 correction note. All findings fixed 2026-10-02, except `PDD-phase3.md` content, which was fixed by its revision on 2026-10-15 (section 5) |
| `scope/clive-scope.md` | Keep as historical. Original `Clive_Scope.txt`, added 2026-10-01 (decision 1) |
| `scope/master-project-document.md` | Keep as historical. Original master project document, added 2026-10-01 (decision 1) |
| `scope/scope-rev2.md` | Keep as historical (superseded by `roadmap.md`). Done 2026-10-05: renamed from `scope/scope&readmap-rev2.md` (no `&` in filenames) |
| `documentation-change-list.md` | Phase 3B documentation change list (2026-10-09, reconciled 2026-10-13). Worked through by course correction W6; items are ticked with the commit that did them. Historical once W6 closes |
| `sprints/course-correction/README.md`, `W1-…` to `W6-…` | Course correction task files (added 2026-10-13). Plans, not records of what happened: results are in `STATUS.md` and `CHANGELOG.md`. 2026-10-19: W2–W4 send client-derived outputs to the private store or git-ignored `evaluation/` files (public-release T7). 2026-10-21: W3 T1 acceptance box ticked. 2026-10-23: W3 T2 box ticked |
| `sprints/public-release/public-release-split.md` | Public-release sprint plan (added 2026-10-19). A plan, not a record: results are in `STATUS.md` and `CHANGELOG.md`. 2026-10-19: T7 decision recorded (Alex). 2026-10-21: T8–T10 results and the T10 re-run decision recorded. 2026-10-21: T10 re-run checks, T11, T12 and T14 recorded; acceptance criteria ticked except the live-test guard and T13. 2026-10-21: T13 recorded, live-test guard re-verified, sprint complete |
| `sprints/course-correction/merge-inputs/ADR-index-additions.md`, `CLAUDE-root-additions.md` | Merge inputs, merged into `ADR/ADR-index.md` (W6 T3) and root `CLAUDE.md` (W6 T6). Kept for history |
| `reviews/kb-audit-2026-10.md` | Historical (review). Knowledge base audit, course correction W3; §1 (current state) written 2026-10-21 by T1; §2–§4 follow from T2–T4. Public: no names, neutral labels only (ADR-017). 2026-10-23: §2 (requirement tests) added by T2 |
| `scope/scope-rev3.md` | Keep as historical (superseded by `STATUS.md` and `course-correction-plan.md`, per its header). Added 2026-10-13 at course correction intake |

## 7. Content to relocate

| Content | From | To (to do) |
|---|---|---|
| Client logging usage | `phase3/logging.md` (fragment) | A "Logging" section in `architecture.md`, then delete the fragment |
| Phase status | `README.md`, `architecture.md`, `phase3/phase3-summary.md`, then `roadmap.md` | `STATUS.md` only (moved from `roadmap.md` 2026-10-13); others link to it |
| Test counts | `testing.md`, `development-standards.md` | Remove; give the command instead. Done (verified 2026-10-06): neither document states a test count |

## 8. Decisions (2026-09-29, Alex)

| Decision | Outcome | Done |
|---|---|---|
| Living/historical split (sections 3–7) | Accepted | Index adopted; section 6 done 2026-10-05; `phase3-summary.md` kept historical, not merged (Alex, 2026-10-15); section 7 to do |
| ADR-008 | Withdrawn as a duplicate of ADR-010 | Yes |
| `structure.txt` | Regenerate from tracked files | Yes |
| `scope/initial.md` | Delete (was empty) | Yes |
| `PDD-phase3.md` | Revise now, not at sign-off | Yes (2026-10-15): revised as-built and closed |

### Decisions from the documentation audit (2026-10-01, Alex)

Source: `docs/doc-audit.md`, "Needs your decision".

| # | Decision | Outcome | Done |
|---|---|---|---|
| 1 | Scope source files | `RevisedScope.txt` is `docs/scope/scope-rev2.md` (renamed from `scope&readmap-rev2.md` 2026-10-05); cite that file. Add `Clive_Scope.txt` and the master project document to `docs/scope/` as historical records with kebab-case names. | Yes (2026-10-02): `scope/clive-scope.md`, `scope/master-project-document.md` |
| 2 | Postgres keys | Add `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` to `.env.example` with placeholder values. `.env.example` lists every key needed to install the system. | Yes (verified 2026-10-05): `.env.example` has all three keys with placeholder values |
| 3 | `README.md` | Overview with links; status, tree and sprint template are linked from `roadmap.md`, `structure.txt` and `development-standards.md` §8. | Yes (verified 2026-10-05): `../README.md` is the overview and links to all three |
| 4 | Ruff rules | Root `CLAUDE.md` §7 wins. Docs say new code must be lint-clean and existing debt is tracked. Clearing the existing lint errors is a later code task. | Yes (2026-10-12): cleared by PR #47; the docs were corrected on 2026-10-15 |
| 5 | Unused mock settings | `SIMPRO_MOCK_MOCK_CLIENT_ID` / `_SECRET` documented as unused in `known-issues.md`. Removing them is a later code task. | Yes (2026-10-08): both removed from `Settings` and from `services/simpro_mock/configuration.md`; the `known-issues.md` entry is marked RESOLVED |

Resolved 2026-10-09, and not a documentation decision: ADR-009 (Phase 3 → 4
handoff). Phase 3 is closed; `roadmap.md` records it.

## 9. Instructions for Claude

Not project documentation, listed so they aren't mistaken for it:
`../CLAUDE.md`, `CLAUDE.md` (this folder), `../src/simpro_client/CLAUDE.md`,
`../services/simpro_mock/CLAUDE.md`, `../tests/CLAUDE.md`, `../.claude/`.
