# Document generation value check

> Historical record as of 2026-11-04, commit 4fa3b8d. Not maintained.

Course correction W2 (`docs/sprints/course-correction/W2-docgen-value-check.md`).
This file is public (ADR-017). It holds the document types, their rank and the
proposed 4A/4B marks only. Volumes, hours and respondents are in the untracked private
notes, `docs/simpro/private/doc-generation-value-check.md`.

## Source and method

- T1 was run as a written survey of five staff, covering every team that produces
  documents, instead of interviews. Alex collected the responses.
- The rank uses estimated hours saved per month. For each person, that is documents
  per month × (hours to write one − hours to check a CLIVE draft), summed over
  respondents.
- Where a respondent gave no check time, their figure counts only as an upper bound.
  The rank uses the conservative (net) figure.
- Answers given without a number ("a lot") are not counted.

## Ranking

| Rank | Document type | Proposed phase | Needs Simpro data? |
|---|---|---|---|
| 1 | Quotes | 4B | Partly: previous jobs and site assets |
| 2 | Technical documents (specs, O&M, handover) | 4A | No |
| 3 | Tender responses | 4A | No |
| 4 | Method statements | 4A | No |
| 5 | RAMS | 4A | No |
| — | Contracts | not a candidate | No respondent produces them |

- Ranks 4 and 5 are the least certain. Missing check times mean their upper bounds
  could place them above rank 3.
- Method statements and RAMS are written by the same people from the same sources, so
  they are likely to be built together.

**Comparison: Simpro Q&A (Phase 3B).** The time respondents reported spending on Simpro
look-ups is of the same order as the top-ranked document types. Respondents were split
on which would save more: two said documents, one said Simpro questions, one said both,
and one said documents plus other tasks.

## 4A / 4B split

**Proposed: split Phase 4.**

- **4A** (no Simpro data): technical documents, tender responses, method statements
  and RAMS. Their sources are templates, past documents, datasheets and the writer's
  own knowledge.
- **4B** (Simpro-fed): quotes. Rank 1 alone, and it depends on Phase 3B's gateway
  (ADR-009, ADR-015).

The phase order is decided at the end of the sprint, not here
(`docs/course-correction-plan.md` §6; status in `docs/STATUS.md`).

## Requests outside the document list

Recorded for later scoping, not ranked:

- Two further internal documents, both candidates for 4A.
- Triage of service email that ends by raising a job in Simpro. That is a **write** to
  Simpro, which root `CLAUDE.md` §3 forbids without an approved scope change.
- A public website chat assistant. It is public-facing and depends on Phase 5 security
  work.
