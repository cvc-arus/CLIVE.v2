# Reviews

Reviews, audits and value checks of the project or its documents. Each review
is a **historical record**: it describes what was found at a point in time and
is not rewritten to match later changes. Factual errors get a dated correction
note at the end, and only when Alex asks (`docs/README.md` §1 and §6).

## Rules

- One file per review, lowercase kebab-case, ending in the month or date it
  ran, e.g. `kb-audit-2026-10.md`.
- Start each file with
  `> Historical record as of <date>, commit <hash>. Not maintained.`
- Record the commands actually run and their output (`docs/CLAUDE.md` §3).
- Findings that need action go to their owners: status and risks to
  `docs/STATUS.md`, defects to `docs/known-issues.md`, decisions to an ADR.
  The review links to them rather than tracking them.
- Add every new review to `docs/README.md` §6 in the same commit.

## Planned reviews

Course correction tasks that will write here (`docs/sprints/course-correction/`):

| File | Written by |
|---|---|
| `doc-generation-value-check.md` | W2 T2 |
| `kb-audit-2026-10.md` | W3 T1 (section 1) and T4 |
