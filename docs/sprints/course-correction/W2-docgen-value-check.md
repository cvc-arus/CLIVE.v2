# W2 — Document Generation Value Check

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | — |
| **Owner** | Alex (human-led; Claude Code formats results only) |

## Goal

Find out which documents cost CVC the most time, and which of them need Simpro
data. This decides whether Phase 4 splits into 4A (no Simpro needed) and 4B
(Simpro-fed), and whether 4A should come before Phase 3B.

## Tasks

### T1 — [HUMAN] Interviews
Speak to the people who produce RAMS, quotes, contracts, tender responses,
method statements and technical documents. For each document type ask:

1. How many do you produce per month?
2. How long does one take, start to finish?
3. Which part takes longest or is most frustrating?
4. Where does the information come from? (Simpro, past documents, templates,
   site visit, your head)
5. If a first draft appeared in minutes, how much time would checking and
   correcting it take?
6. Who reviews or signs it off?

### T2 — Record results
Interview figures are CVC business data and stay out of the public
repository (ADR-017; public-release sprint T7, Alex 2026-10-19). Record them
in the untracked private store, `docs/simpro/private/doc-generation-value-check.md`
(created by this task), with one row per document type:

| Document type | Per month | Hours each | Hours if drafted | Est. hours saved/month | Needs Simpro data? | Notes |
|---|---|---|---|---|---|---|

Include Simpro Q&A as a comparison row using the earlier user feedback.
Claude Code can create the file and format notes Alex provides; it must not
invent figures.

### T3 — [HUMAN] Ranking
Rank document types by hours saved per month. Mark the proposed 4A candidates
(no Simpro dependency) and 4B candidates. The tracked review
`docs/reviews/doc-generation-value-check.md` (created by this task) holds the
document types, their rank and the 4A/4B marks only, with no volumes, hours or
names, and links to the private notes for the figures.

## Verification
Every row has figures from at least one interview, or is marked "estimate".

## Rollback
`git revert <commit>`.

## Git commit
`docs(review): document generation value check`

## Acceptance criteria
- [ ] At least 5 people or all document types covered
- [ ] Ranked table committed
- [ ] 4A / 4B split proposed (or rejected with reasons)
- [ ] `STATUS.md` updated
