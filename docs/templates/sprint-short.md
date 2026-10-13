# <Phase> — Sprint <N>: <Title>

> **Short template.** Use for sprints or tasks that do not change
> infrastructure, security, or data (application code, tests, documentation,
> reviews, research). If in doubt, use the full template.

| | |
|---|---|
| **Status** | Draft / Approved / Done |
| **Depends on** | |
| **Related ADRs** | |

## Goal
One or two sentences, including why it matters.

## Tasks
Numbered. Each task: objective, steps, stop point. Mark human-only steps **[HUMAN]**.

## Verification
Commands and expected output.

## Rollback
How to undo (usually `git revert <commit>`).

## Git commit
Conventional commit message.

## Acceptance criteria
Checkable statements. Always include: `docs/STATUS.md` updated.
