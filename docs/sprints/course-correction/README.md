# Course Correction Sprint — Task Files

Plan: `docs/course-correction-plan.md` · Status: `docs/STATUS.md`

## How to run a task with Claude Code

1. Start a fresh Claude Code session in the repo root (keeps context focused).
2. Run `/sprint-task docs/sprints/course-correction/<file> <task id>`
   e.g. `/sprint-task docs/sprints/course-correction/W6-docs-consolidation.md T1`
3. Claude Code restates the task, does it, runs the verification, reports
   results, proposes a commit message, and stops.
4. Review the diff. If satisfied, tell Claude Code to commit.
5. Run `/status-update` to record the result in `docs/STATUS.md`.
6. Move to the next task in a new session.

Tasks marked **[HUMAN]** are yours. Claude Code will stop and list them.

## Order

| Day | Task |
|---|---|
| 1 | W6 T1 · W1 T1 [HUMAN] |
| 2–3 | W5 T1 → T6 |
| 4–5 | W6 T2 → T7 · W1 T2–T3 |
| 6–7 | W3 T1 → T4 |
| 8–9 | W4 T1 → T4 |
| 6–10 | W2 T1 → T3 [HUMAN] alongside |
| 10 | Decision point [HUMAN] |

## Files

| File | Workstream | Template |
|---|---|---|
| `W1-simpro-access.md` | Simpro access and live API checks | Short |
| `W2-docgen-value-check.md` | Document generation value check | Short |
| `W3-kb-audit.md` | Knowledge base audit | Short |
| `W4-evaluation.md` | Evaluation set and baseline | Short |
| `W5-backups.md` | Backups and restore drill | Full |
| `W6-docs-consolidation.md` | Documentation consolidation, Phase 3 sign-off | Short |

## Rules for every task (added to root `CLAUDE.md` by W6 T6)

- One task per session. Stop after verification; never continue to the next task.
- Never print or commit secrets; reference `.env` variable names only.
- Ask before any destructive action: removing volumes or containers with data,
  dropping databases, deleting or overwriting backups, `git push --force`,
  rewriting history, or editing historical documents (`docs/README.md` §6).
- Host-level changes (packages, systemd, cron, firewall) need explicit approval.
- If the task file and the codebase disagree, stop and report; the code is the
  source of truth.
