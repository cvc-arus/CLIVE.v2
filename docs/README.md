# CLIVE Documentation Index

> **Status: PROPOSED.** Drafted for Alex's review from the repository at
> commit `31936f8`. Items marked *Proposed* are not yet decided. Edit this
> file, then remove this note once the structure is agreed.

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

| Document | Owns | Current state (at `31936f8`) |
|---|---|---|
| `../README.md` | Project overview, links into `docs/` | Stale: Phase 3 shown as Planned; out-of-date tree |
| `roadmap.md` | Phase list and phase status *(Proposed: the only place phase status is stated)* | Stale: says typed layer not started |
| `architecture.md` | Services, ports, containers, `simpro_client` and `simpro_mock` design | Stale: typed layer and rate limiter listed as absent |
| `installation.md` | Setting up and running the stack | Not yet reviewed against current code |
| `development-standards.md` | Coding, tooling, Git, sprint template | Stale: 18 tests, deleted test file |
| `testing.md` | Test layers, markers, how to run them | Stale: 18 tests, deleted test file |
| `known-issues.md` | Open discrepancies and defects | Stale: #6 contradicted by code; resolved items mixed with open ones |
| `CHANGELOG.md` | What changed, per sprint | Needs Sprint 4 entries |

## 4. Reference documents (regenerate, don't hand-edit)

| Document | Generated from |
|---|---|
| `simpro-mock-api-reference.md` | `services/simpro_mock/simpro_mock/routers.py`, `schemas.py`, `filtering.py`, `middleware.py` |
| `../services/simpro_mock/configuration.md` | `services/simpro_mock/simpro_mock/config.py` |
| `../structure.txt` | `tree -L 4 -I '.git|.venv|__pycache__|*.egg-info'` *(Proposed: or delete, since `architecture.md` covers layout)* |

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
| `ADR/adr-010-resilience-policy.md` | Approved; implemented with deviations (see `../src/simpro_client/CLAUDE.md`) |
| `ADR/adr-mock-simpro-api.md` | Capability list predates the 12-resource mock |
| `ADR/adr-008-rate-limiting-strategy.md` | **Decision needed:** its text duplicates ADR-010 |
| `PDDs/PDD-phase1.md`, `PDD-phase2.md` | Phases complete |
| `PDDs/PDD-phase3.md` | "As-built" at 2026-09-04; predates Sprint 4. Revise at Phase 3 sign-off |
| `PDDs/PDD-phase4.md` | Draft. Links to a non-existent `adr-006-phase3-phase4-handoff.md` (should be ADR-009) |

## 6. Historical documents

Phase 3 documents now use a `phase3-` prefix (commit `31936f8`). *Proposed:*
also move the sprint records into `docs/phase3/sprints/`, keeping the prefixed
names, so they are visibly separate from living documents. Each gets a
one-line header: `> Historical record as of <date>, commit <hash>. Not maintained.`

| Current path | Proposed action |
|---|---|
| `phase1/summary.md` | Keep as historical. Its `docker exec -it ollama` commands fail (container is `clive-ollama`); add a correction note or move usable commands into `installation.md` |
| `phase2/summary.md` | Keep as historical |
| `phase3/phase3-summary.md` | Merge anything still current into `architecture.md` / `testing.md`, then keep as the Phase 3 historical summary |
| `phase3/phase3-sprint4-contract.md` | Move to `phase3/sprints/`. Still the reference spec for Sprint 4 |
| `phase3/phase3-sprint4-preflight-audit.md` | Move to `phase3/sprints/` |
| `phase3/phase3-sprint4-architecture-summary.md` | Move to `phase3/sprints/` (baseline snapshot) |
| `phase3/phase3-sprint4-2-typed-python-SDK-endpoint-layer.md` | Move to `phase3/sprints/`; add correction note (claims don't match the repository) |
| `phase3/phase3-sprint4-4-pagiantion and retries.md` | Move and rename to `phase3/sprints/phase3-sprint4-4-pagination-and-retries.md` (no spaces, typo fixed) |
| `phase3/phase3-sprint4.md` | Chat fragment duplicating the contract's test sequence. Delete after checking nothing unique is lost |
| `scope/scope&readmap-rev2.md` | Keep as historical (superseded by `roadmap.md`). Rename to `scope/scope-rev2.md` (no `&` in filenames) |
| `scope/initial.md` | Empty file. Either paste in the original `Clive_Scope.txt` (a project file, not currently in the repository) as a record, or delete |

## 7. Content to relocate

| Content | From | To (Proposed) |
|---|---|---|
| Client logging usage | `phase3/logging.md` (fragment) | A "Logging" section in `architecture.md`, then delete the fragment |
| Phase status | `README.md`, `architecture.md`, `phase3/phase3-summary.md` | `roadmap.md` only; others link to it |
| Test counts | `testing.md`, `development-standards.md` | Remove; give the command instead |

## 8. Decisions waiting on Alex

1. Adopt the living/historical split above, or amend it.
2. ADR-008 vs ADR-010: withdraw ADR-008, or rewrite it as the original
   rate-limiting proposal and mark it superseded by ADR-010.
3. `structure.txt`: regenerate or delete.
4. `scope/initial.md`: fill or delete.
5. Whether `PDD-phase3.md` is revised now or at Phase 3 sign-off.

ADR-009 (Phase 3 → 4 handoff) is also open, but it is not a documentation
decision and does not block this tidy-up.

## 9. Instructions for Claude

Not project documentation, listed so they aren't mistaken for it:
`../CLAUDE.md`, `CLAUDE.md` (this folder), `../src/simpro_client/CLAUDE.md`,
`../services/simpro_mock/CLAUDE.md`, `../tests/CLAUDE.md`, `../.claude/`.
