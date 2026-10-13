<!--
Merge into the existing docs/ADR/ADR-index.md (W6 T3). This file stays in
docs/sprints/course-correction/merge-inputs/; do not copy it into docs/ADR/.
-->

## Naming convention

| Rule | Example |
|---|---|
| File name: `adr-NNN-short-kebab-title.md`, lowercase, number zero-padded to three digits | `adr-014-simpro-access-control-model.md` |
| Heading: `# ADR-NNN: Title` | `# ADR-014: Simpro data access control model` |
| References in any document: `ADR-NNN` | "per ADR-010" |

Exceptions kept for existing links: `ADR-index.md` (this file) and the
unnumbered legacy `adr-mock-simpro-api.md`. Renaming either needs Alex's approval.

## Numbering rules

1. **Next number = highest number in this index + 1.** Check this index, the
   `docs/ADR/` folder and open branches or pull requests before assigning.
2. **Assign the number at commit time, in the repo.** Drafts written outside
   the repo (e.g. in a Claude chat) use the placeholder `ADR-XXX` in the file
   name, heading and references. Claude Code replaces it with the next free
   number when committing, and updates every reference.
3. **Reserve the number in the same commit:** add the index row with the ADR file.
4. **Numbers are never reused.** Withdrawn and superseded ADRs keep their file
   and number, with their status updated.
5. **Accepted ADRs are not rewritten.** Change them with a new ADR that
   supersedes them, and update only the old ADR's Status line
   (`docs/CLAUDE.md` §4).

## Statuses

`Proposed` · `Accepted` / `Approved` · `Superseded by ADR-NNN` · `Rejected` ·
`Withdrawn` (with a reason), as in `docs/CLAUDE.md` §4.
Only Alex changes a status to `Accepted`.

## New index rows

In the index's existing columns. The gateway as the single Simpro access point
is ADR-009 (already in the index); it gets no new row.

| # | Title | Phase | Status |
|---|---|---|---|
| 014 | Simpro Data Access Control Model (`adr-014-simpro-access-control-model.md`) | 3B | Proposed (2026-10-09). Conflict for Alex to resolve: `clive_gateway` storage on the Phase 2 Postgres vs root `CLAUDE.md` §3 |
| 015 | Conversational Access Approach for Simpro Data (`adr-015-conversational-access-approach.md`) | 3B | Proposed (2026-10-09) |

**Next free number:** ADR-016
