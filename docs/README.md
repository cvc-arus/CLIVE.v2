# CLIVE Documentation Index

> **Status: adopted 2026-09-29.** Structure agreed by Alex. Section 6 and 7
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

| Document | Owns | Current state (at `31936f8`) |
|---|---|---|
| `../README.md` | Project overview, links into `docs/` | Stale: Phase 3 shown as Planned; out-of-date tree |
| `roadmap.md` | Phase list and phase status (the only place phase status is stated) | Stale: says typed layer not started |
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
| `ADR/adr-010-resilience-policy.md` | Approved; implemented with deviations (see `../src/simpro_client/CLAUDE.md`) |
| `ADR/adr-mock-simpro-api.md` | Capability list predates the 12-resource mock |
| `ADR/adr-008-rate-limiting-strategy.md` | Withdrawn 2026-09-29 (duplicate of ADR-010). Kept for history |
| `PDDs/PDD-phase1.md`, `PDD-phase2.md` | Phases complete |
| `PDDs/PDD-phase3.md` | "As-built" at 2026-09-04; predates Sprint 4. **To do: revise now** (decided 2026-09-29) |
| `PDDs/PDD-phase4.md` | Draft. Links to a non-existent `adr-006-phase3-phase4-handoff.md` (should be ADR-009) |

## 6. Historical documents

Phase 3 documents use a `phase3-` prefix. Sprint records move into
`docs/phase3/sprints/`, keeping the prefixed names, so they are visibly
separate from living documents. Each gets a one-line header:
`> Historical record as of <date>, commit <hash>. Not maintained.`

| Current path | Action (to do) |
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

## 7. Content to relocate

| Content | From | To (to do) |
|---|---|---|
| Client logging usage | `phase3/logging.md` (fragment) | A "Logging" section in `architecture.md`, then delete the fragment |
| Phase status | `README.md`, `architecture.md`, `phase3/phase3-summary.md` | `roadmap.md` only; others link to it |
| Test counts | `testing.md`, `development-standards.md` | Remove; give the command instead |

## 8. Decisions (2026-09-29, Alex)

| Decision | Outcome | Done |
|---|---|---|
| Living/historical split (sections 3–7) | Accepted | Index adopted; section 6–7 moves to do |
| ADR-008 | Withdrawn as a duplicate of ADR-010 | Yes |
| `structure.txt` | Regenerate from tracked files | Yes |
| `scope/initial.md` | Delete (was empty) | Yes |
| `PDD-phase3.md` | Revise now, not at sign-off | To do |

Still open, but not a documentation decision: ADR-009 (Phase 3 → 4
handoff).

## 9. Instructions for Claude

Not project documentation, listed so they aren't mistaken for it:
`../CLAUDE.md`, `CLAUDE.md` (this folder), `../src/simpro_client/CLAUDE.md`,
`../services/simpro_mock/CLAUDE.md`, `../tests/CLAUDE.md`, `../.claude/`.
