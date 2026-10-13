<!--
Merge into the existing docs/ADR/ADR-index.md (W6 T3). Do not copy this file into docs/ADR/.
-->

## Naming convention

| Rule | Example |
|---|---|
| File name: `adr-NNN-short-kebab-title.md`, lowercase, number zero-padded to three digits | `adr-014-simpro-access-mechanism.md` |
| Heading: `# ADR-NNN: Title` | `# ADR-014: Simpro access mechanism (gateway as single access point)` |
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
5. **Accepted ADRs are not rewritten.** Change them with a dated
   `## Amendment (YYYY-MM-DD)` section, or a new ADR that supersedes them.

## Statuses

`Proposed` · `Accepted` · `Superseded by ADR-NNN` · `Withdrawn` · `Deprecated`.
Only Alex changes a status to `Accepted`.

## New index rows

| ADR | Title | Status | Date | File |
|---|---|---|---|---|
| ADR-014 | Simpro access mechanism (gateway as single access point) | Proposed | 2026-10-09 | `adr-014-simpro-access-mechanism.md` |
| ADR-015 | Simpro data access control model | Proposed | 2026-10-09 | `adr-015-simpro-access-control-model.md` |
| ADR-016 | Conversational access approach for Simpro data | Proposed | 2026-10-09 | `adr-016-conversational-access-approach.md` |

**Next free number:** ADR-017
