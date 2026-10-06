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
- **No volatile numbers in living documents.** Test counts, lint error
  counts and commit hashes go stale. Give the command to run instead.
  Historical documents may record numbers, with the commit they came from.
- **Planned is not implemented.** Anything not in the code is labelled
  *Planned* or *Proposed* with a pointer to where it is planned.
- Evidence and style rules for editing are in `docs/CLAUDE.md`.

## 3. Living documents

| Document | Owns | Current state (re-verify before relying on this) |
|---|---|---|
| `../README.md` | Project overview, links into `docs/` | Rewritten 2026-10-05 as the project overview (purpose, modules, architecture, services, documentation map); status, tree and install steps are links to their owners |
| `roadmap.md` | Phase list and phase status (the only place phase status is stated) | Fixed 2026-10-02 (`doc-audit.md`): Phase 3 typed layer shown as implemented; remaining work is ADR-009 and sign-off. 2026-10-05: Phase 4 handoff mechanism now deferred to ADR-009 |
| `architecture.md` | Services, ports, containers, `simpro_client` and `simpro_mock` design | Fixed 2026-10-02 (`doc-audit.md`): typed layer, rate limiter, exception hierarchy and response handling match `client.py`. 2026-10-05: port table (all `127.0.0.1`), volumes, mock DB `.env` keys and healthchecks match `docker-compose.yml`. 2026-10-06: mock base image tag matches `services/simpro_mock/Dockerfile`. 2026-10-06: response handling updated for transient-error retries (ADR-010 §2.2) |
| `installation.md` | Setting up and running the stack | Fixed 2026-10-02 (`doc-audit.md`). Docker steps not re-run. 2026-10-05: `SIMPRO_MOCK_DB_*` keys and localhost-only ports added |
| `development-standards.md` | Coding, tooling, Git, sprint template | Fixed 2026-10-02 (`doc-audit.md`) |
| `testing.md` | Test layers, markers, how to run them | Fixed 2026-10-02 (`doc-audit.md`): all test modules listed, no counts. 2026-10-06: `test_retries.py` row covers transient-error retries |
| `known-issues.md` | Open discrepancies and defects | Fixed 2026-10-02 (`doc-audit.md`): stale Sprint 4 entry removed; unused mock settings and lint debt added. 2026-10-05: date removed from title (each entry keeps its own) |
| `CHANGELOG.md` | What changed, per sprint | Fixed 2026-10-02 (`doc-audit.md`): Sprint 4 entry added. 2026-10-05: shallow-history caveat removed from intro |

## 4. Reference documents (regenerate, don't hand-edit)

| Document | Generated from |
|---|---|
| `simpro-mock-api-reference.md` | `services/simpro_mock/simpro_mock/routers.py`, `schemas.py`, `filtering.py`, `middleware.py` |
| `../services/simpro_mock/configuration.md` | `services/simpro_mock/simpro_mock/config.py` |
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
| `ADR/adr-009-phase3-phase4-handoff.md` | Open decision |
| `ADR/adr-010-resilience-policy.md` | Accepted, implemented with deviations (see `../src/simpro_client/CLAUDE.md`) |
| `ADR/adr-mock-simpro-api.md` | Capability list predates the 12-resource mock |
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
| Phase status | `README.md`, `architecture.md`, `phase3/phase3-summary.md` | `roadmap.md` only; others link to it |
| Test counts | `testing.md`, `development-standards.md` | Remove; give the command instead |

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
| 5 | Unused mock settings | `SIMPRO_MOCK_MOCK_CLIENT_ID` / `_SECRET` documented as unused in `known-issues.md`. Removing them is a later code task. | To do |

Still open, but not a documentation decision: ADR-009 (Phase 3 → 4
handoff).

## 9. Instructions for Claude

Not project documentation, listed so they aren't mistaken for it:
`../CLAUDE.md`, `CLAUDE.md` (this folder), `../src/simpro_client/CLAUDE.md`,
`../services/simpro_mock/CLAUDE.md`, `../tests/CLAUDE.md`, `../.claude/`.
