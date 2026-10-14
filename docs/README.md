# CLIVE Documentation Index

> **Status: adopted 2026-09-29.** Structure agreed by Alex. Section 6 actions
> are done (2026-10-05) except the `phase3-summary.md` merge; section 7
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
- Evidence and style rules for editing are in `docs/CLAUDE.md`.

## 3. Living documents

| Document | Owns | Current state (re-verify before relying on this) |
|---|---|---|
| `../README.md` | Project overview, links into `docs/` | Rewritten 2026-10-05 as the project overview (purpose, modules, architecture, services, documentation map); status, tree and install steps are links to their owners. 2026-10-06: services table marks every port localhost-only; licence sentence removed. 2026-10-13: status pointers name `docs/STATUS.md`; `roadmap.md` is linked for phases and scope |
| `STATUS.md` | Current status: phases, current sprint and workstreams, Simpro access, open risks, ADRs awaiting a decision (the only place status is stated) | Added 2026-10-13 with the course correction package (PR #49). 2026-10-13: became the sole owner of status (W6 T1); Phase 3 row links to `phase3/phase3-signoff.md` |
| `roadmap.md` | Phase list and phase scope (status is in `STATUS.md`) | Fixed 2026-10-02 (`doc-audit.md`): Phase 3 typed layer shown as implemented; remaining work is ADR-009 and sign-off. 2026-10-05: Phase 4 handoff mechanism now deferred to ADR-009. 2026-10-08: "Phase 3 — Remaining Work" records ADR-013 as implemented, names `test_spec_conformance.py` and the two integration modules, and adds a defect-triage item pointing at `known-issues.md`. 2026-10-08: that item no longer lists the two mock query defects, which were fixed. 2026-10-12: Phase 3 marked closed 2026-10-09, Phase 4 no longer blocked, "Remaining Work" replaced by a close-out section, and the Phase 4 entry criteria and planned-scope rows updated for ADR-009's decision. 2026-10-13: Status column replaced by a link to `STATUS.md`, which now owns status (course correction W6 T1); the Phase 4 note no longer states status |
| `architecture.md` | Services, ports, containers, `simpro_client` and `simpro_mock` design | Fixed 2026-10-02 (`doc-audit.md`): typed layer, rate limiter, exception hierarchy and response handling match `client.py`. 2026-10-05: port table (all `127.0.0.1`), volumes, mock DB `.env` keys and healthchecks match `docker-compose.yml`. 2026-10-06: mock base image tag matches `services/simpro_mock/Dockerfile`. 2026-10-06: response handling updated for transient-error retries (ADR-010 §2.2); `auth.py` token requests go through the rate limiter; `SimproAuthRefreshError` added. 2026-10-06: `SimproAuthError` context fields (ADR-011); ADR-011 accepted. 2026-10-06: `config.py` row covers per-`auth_mode` validation; `company_id_service` / `company_id_projects` marked reserved. 2026-10-06: header says maintained since 2026-09-04. 2026-10-06: response handling records the `SIMPRO_MAX_RETRY_DELAY` cap on `Retry-After` (ADR-012). 2026-10-07: `auth.py` row and the `401` row record the refresh lock and token-aware invalidate (ADR-012 §2.2). 2026-10-07: §5.2 route count, §5.3 data model and §5.4 endpoint table updated for the ADR-013 S2 route corrections (Projects removed, attachments and status codes re-pathed). 2026-10-08: §5.1–§5.5 rewritten for the completed ADR-013 re-shape and re-verified against the code — module layout, 16 ORM classes / 17 tables, the 25-route surface with the three polymorphic customer routes, the dropped `projects` table, the `serializers.py` / `projection.py` layers, per-model filter maps and the 400 on an unknown filter. Counts in §5.1 and §5.2 were taken by importing the packages on 2026-10-08. 2026-10-08: §5.4 gained an Ordering paragraph for the new `ordering.py` (`orderby`, the 400 on an unorderable field, the `id` ordering that pagination needs, and `limit`). 2026-10-13: intro points at `STATUS.md` for phase status (W6 T1) |
| `installation.md` | Setting up and running the stack | Fixed 2026-10-02 (`doc-audit.md`). Docker steps not re-run. 2026-10-05: `SIMPRO_MOCK_DB_*` keys and localhost-only ports added. 2026-10-06: prerequisites name `uv` only; diagnostic run with `uv run`; mock started with `--build` 2026-10-14: §9 Backups rewritten for the extended `scripts/backup.sh` (W5 T3). |
| `development-standards.md` | Coding, tooling, Git, sprint template | Fixed 2026-10-02 (`doc-audit.md`). 2026-10-06: branch-naming convention added (§7); §2 run commands corrected to `uv run`. 2026-10-06: `client.py` docstring remark removed (§1); feature branches merge to `develop` (§7) |
| `testing.md` | Test layers, markers, how to run them | Fixed 2026-10-02 (`doc-audit.md`): all test modules listed, no counts. 2026-10-06: `test_retries.py` row covers transient-error retries; `test_auth.py` row covers limiter use; `test_retries.py` row covers refresh failure. 2026-10-06: auth-error context in `test_auth.py` / `test_retries.py` rows. 2026-10-06: mock-start and diagnostic commands corrected (`--build`, `uv run`). 2026-10-06: `test_config.py` row covers `auth_mode` validation. 2026-10-06: diagnostic script line count removed; `test_auth.py` / `test_retries.py` rows list every test. 2026-10-07: §1 gained a `test_spec_conformance.py` row and §3 now covers both integration modules, including `test_client_mock_drift.py` (ADR-013). 2026-10-07: §4 resource count corrected to 11 served resources. 2026-10-08: §1, §3 and §4 updated for ADR-013 S3–S6 — `test_spec_conformance.py` records the empty baseline, `test_models.py`/`test_endpoints.py`/`test_route_contract.py` rows cover their new assertions, §3 lists the S6 query-handling and drift tests, and §4's resource count became a route count. 2026-10-08: §3's `test_simpro_mock_v2.py` row lists the six new `orderby` / `limit` / page-determinism tests |
| `recovery-plan.md` | Recovery plan: data location per disk, backup target, backup inventory and procedure, restore procedure and drill reports | Added 2026-10-14 (course correction W5 T1): disk layout, live data per disk, the six unmounted `/data` directories, and the backup target `<home>/clive-backups/`; later sections are placeholders for W5 T2–T7. 2026-10-14: §7 backup inventory added (W5 T2); §6 records the `postgres:16-alpine` archiving decision 2026-10-14: §8 backup procedure and first-run evidence added (W5 T3); §7 marks `.env` as deferred. |
| `known-issues.md` | Open discrepancies and defects | Fixed 2026-10-02 (`doc-audit.md`): stale Sprint 4 entry removed; unused mock settings and lint debt added. 2026-10-05: date removed from title (each entry keeps its own). 2026-10-08: added the cutover-claim entry, marked RESOLVED by ADR-013, with the two caveats that remain unverifiable without live access; the preamble now says resolved entries are marked rather than deleted. 2026-10-08: added two entries — the mock accepts and ignores `orderby` and `limit`, and collection routes paginate without an `ORDER BY` — then marked both RESOLVED the same day when they were fixed, carrying forward one caveat (`limit`'s upstream semantics are unverified). 2026-10-08: the unused mock settings entry marked RESOLVED when the two fields were removed |
| `CHANGELOG.md` | What changed, per sprint | Fixed 2026-10-02 (`doc-audit.md`): Sprint 4 entry added. 2026-10-05: shallow-history caveat removed from intro. 2026-10-06: entries added for the compose hardening, `verify.sh`, deterministic seed and mock `Dockerfile` changes. 2026-10-06: entry added for the ADR-012 retry delay ceiling. 2026-10-07: entry added for the `AuthManager` refresh lock. 2026-10-07: entries added for ADR-013 (drafted, then accepted), the vendored Simpro contract and the two new test modules, and for the S2 route corrections. 2026-10-08: entries added for ADR-013 S3–S7 — the three re-shape waves, the mock's `columns` projection and loud filtering, and the documentation close-out, and for the post-close-out corrections to `CLAUDE.md` §4, this file and `roadmap.md`. 2026-10-08: entry added for the mock's `orderby` / `limit` implementation and its now-deterministic pagination. 2026-10-12: entries added for ADR-009's decision and for closing Phase 3. 2026-10-13: entry added for the course correction sprint start and `STATUS.md` taking over status |

## 4. Reference documents (regenerate, don't hand-edit)

| Document | Generated from |
|---|---|
| `simpro-mock-api-reference.md` | `services/simpro_mock/simpro_mock/routers.py`, `schemas.py`, `serializers.py`, `filtering.py`, `projection.py`, `middleware.py`. Routes **and** field sets are spec-derived (ADR-013), with the conformance baseline empty as of S5; §4 covers the S6 `columns` projection and per-resource filter maps |
| `contracts/simpro-openapi-v1-get-subset.json` | Simpro's published OpenAPI 2.0 spec, pruned to the GET operations CLIVE reads. Regenerate with `uv run python scripts/prune-simpro-spec.py <full-spec.json> docs/contracts/simpro-openapi-v1-get-subset.json`. Normative for model field names, types and optionality (ADR-013); enforced by `tests/test_spec_conformance.py` |
| `../services/simpro_mock/configuration.md` | `services/simpro_mock/simpro_mock/config.py` |
| `contracts/simpro-openapi-v1-get-subset.json` | Simpro's published OpenAPI 2.0 spec, pruned to the 25 GET paths this project uses (ADR-013). **Normative** for field names, types and optionality. Regenerate from a vendor drop with `scripts/prune-simpro-spec.py`; do not hand-edit |
| `../structure.txt` | Tracked files only. Regenerate from the repo root after adding, moving or deleting files (needs `tree` ≥ 2.0): |

```bash
{ echo "# Generated from 'git ls-files'. Do not edit by hand; regenerate with the command in docs/README.md."; git ls-files | grep -vE '__pycache__|\.egg-info/' | tree --fromfile . --charset=utf-8 -a; } > structure.txt
```

## 5. Decision documents

| Document | Notes |
|---|---|
| `ADR/ADR-index.md` | Owns ADR status. Must list every ADR. |
| `ADR/adr-001-local-llm-stack.md` | Phase 1 |
| `ADR/adr-002-vector-database-pgvector.md` | Phase 2 |
| `ADR/adr-003-document-extraction-tika.md` | Phase 2 |
| `ADR/adr-004-http-client-choice.md` | Phase 3 |
| `ADR/adr-005-auth-strategy.md` | Phase 3 |
| `ADR/adr-006-library-first-architecture.md` | Phase 3 |
| `ADR/adr-007-configuration-management.md` | Phase 3 |
| `ADR/adr-009-phase3-phase4-handoff.md` | Decision recorded 2026-10-09 (Alex): Option B, a single `clive-gateway` service imports `simpro_client` and serves every other consumer over HTTP. Status line still reads Proposed; partially supersedes ADR-006's "no service wrapper" |
| `ADR/adr-010-resilience-policy.md` | Accepted, implemented with deviations (see `../src/simpro_client/CLAUDE.md`); §2.5 superseded by ADR-011 |
| `ADR/adr-011-exception-hierarchy-and-auth-errors.md` | Accepted 2026-10-06, implemented (supersedes ADR-010 §2.5) |
| `ADR/adr-012-retry-delay-ceiling-and-auth-concurrency.md` | Accepted 2026-10-06 (supersedes ADR-010 §2.3, extends §2.1) |
| `ADR/adr-013-reshape-to-published-simpro-spec.md` | Accepted 2026-10-07, implemented 2026-10-08 (all 7 sprints). Governs field names, types and optionality via `contracts/simpro-openapi-v1-get-subset.json`; supersedes `adr-mock-simpro-api.md` "Capabilities & Coverage" |
| `ADR/adr-mock-simpro-api.md` | Decision stands; its "Capabilities & Coverage" list is superseded by ADR-013 |
| `ADR/adr-008-rate-limiting-strategy.md` | Withdrawn 2026-09-29 (duplicate of ADR-010). Kept for history |
| `PDDs/PDD-phase1.md`, `PDD-phase2.md` | Phases complete |
| `PDDs/PDD-phase3.md` | "As-built" at 2026-09-04; predates Sprint 4. **To do: revise now** (decided 2026-09-29) |
| `PDDs/PDD-phase4.md` | Draft. Handoff link fixed 2026-10-02 (now ADR-009) |

## 6. Historical documents

Phase 3 documents use a `phase3-` prefix. Sprint records move into
`docs/phase3/sprints/`, keeping the prefixed names, so they are visibly
separate from living documents. Each gets a one-line header:
`> Historical record as of <date>, commit <hash>. Not maintained.`

| Current path | Action / status |
|---|---|
| `phase1/summary.md` | Keep as historical. Done 2026-10-05: correction note added (container is `clive-ollama`; original commands unchanged) |
| `phase2/summary.md` | Keep as historical |
| `phase3/phase3-summary.md` | Keep as the Phase 3 historical summary. Checked 2026-10-05 for content still current and not in `architecture.md` / `testing.md`; merging waits for Alex's decision |
| `phase3/phase3-signoff.md` | Historical. Phase 3 sign-off evidence (close, test run at commit `8b11657`, items carried past the close), added 2026-10-13 (W6 T1) |
| `phase3/sprints/phase3-sprint4-contract.md` | Done 2026-10-05: moved to `phase3/sprints/`. Still the reference spec for Sprint 4 |
| `phase3/sprints/phase3-sprint4-preflight-audit.md` | Done 2026-10-05: moved to `phase3/sprints/` |
| `phase3/sprints/phase3-sprint4-architecture-summary.md` | Done 2026-10-05: moved to `phase3/sprints/` (baseline snapshot) |
| `phase3/sprints/phase3-sprint4-2-typed-python-sdk-endpoint-layer.md` | Done 2026-10-05: moved to `phase3/sprints/`, renamed (lowercase `sdk`), correction note added (claims don't match the repository) |
| `phase3/sprints/phase3-sprint4-4-pagination-and-retries.md` | Done 2026-10-05: moved to `phase3/sprints/` |
| `phase3/sprints/phase3-sprint4.md` | Done 2026-10-05: moved to `phase3/sprints/` and kept as historical (not deleted). Chat fragment duplicating the contract's test sequence |
| `doc-audit.md` | Keep as historical. Full `/doc-check all` report of 2026-10-01, with a 2026-10-02 correction note. All findings fixed 2026-10-02, except `PDD-phase3.md` content, which waits for its planned revision (section 5) |
| `scope/clive-scope.md` | Keep as historical. Original `Clive_Scope.txt`, added 2026-10-01 (decision 1) |
| `scope/master-project-document.md` | Keep as historical. Original master project document, added 2026-10-01 (decision 1) |
| `scope/scope-rev2.md` | Keep as historical (superseded by `roadmap.md`). Done 2026-10-05: renamed from `scope/scope&readmap-rev2.md` (no `&` in filenames) |

## 7. Content to relocate

| Content | From | To (to do) |
|---|---|---|
| Client logging usage | `phase3/logging.md` (fragment) | A "Logging" section in `architecture.md`, then delete the fragment |
| Phase status | `README.md`, `architecture.md`, `phase3/phase3-summary.md`, then `roadmap.md` | `STATUS.md` only (moved from `roadmap.md` 2026-10-13); others link to it |
| Test counts | `testing.md`, `development-standards.md` | Remove; give the command instead. Done (verified 2026-10-06): neither document states a test count |

## 8. Decisions (2026-09-29, Alex)

| Decision | Outcome | Done |
|---|---|---|
| Living/historical split (sections 3–7) | Accepted | Index adopted; section 6 done 2026-10-05 (except `phase3-summary.md` merge); section 7 to do |
| ADR-008 | Withdrawn as a duplicate of ADR-010 | Yes |
| `structure.txt` | Regenerate from tracked files | Yes |
| `scope/initial.md` | Delete (was empty) | Yes |
| `PDD-phase3.md` | Revise now, not at sign-off | To do |

### Decisions from the documentation audit (2026-10-01, Alex)

Source: `docs/doc-audit.md`, "Needs your decision".

| # | Decision | Outcome | Done |
|---|---|---|---|
| 1 | Scope source files | `RevisedScope.txt` is `docs/scope/scope-rev2.md` (renamed from `scope&readmap-rev2.md` 2026-10-05); cite that file. Add `Clive_Scope.txt` and the master project document to `docs/scope/` as historical records with kebab-case names. | Yes (2026-10-02): `scope/clive-scope.md`, `scope/master-project-document.md` |
| 2 | Postgres keys | Add `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` to `.env.example` with placeholder values. `.env.example` lists every key needed to install the system. | Yes (verified 2026-10-05): `.env.example` has all three keys with placeholder values |
| 3 | `README.md` | Overview with links; status, tree and sprint template are linked from `roadmap.md`, `structure.txt` and `development-standards.md` §8. | Yes (verified 2026-10-05): `../README.md` is the overview and links to all three |
| 4 | Ruff rules | Root `CLAUDE.md` §7 wins. Docs say new code must be lint-clean and existing debt is tracked. Clearing the existing lint errors is a later code task. | To do |
| 5 | Unused mock settings | `SIMPRO_MOCK_MOCK_CLIENT_ID` / `_SECRET` documented as unused in `known-issues.md`. Removing them is a later code task. | Yes (2026-10-08): both removed from `Settings` and from `services/simpro_mock/configuration.md`; the `known-issues.md` entry is marked RESOLVED |

Resolved 2026-10-09, and not a documentation decision: ADR-009 (Phase 3 → 4
handoff). Phase 3 is closed; `roadmap.md` records it.

## 9. Instructions for Claude

Not project documentation, listed so they aren't mistaken for it:
`../CLAUDE.md`, `CLAUDE.md` (this folder), `../src/simpro_client/CLAUDE.md`,
`../services/simpro_mock/CLAUDE.md`, `../tests/CLAUDE.md`, `../.claude/`.
