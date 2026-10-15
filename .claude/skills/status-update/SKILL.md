---
name: status-update
description: Record a completed CLIVE task in docs/STATUS.md and docs/CHANGELOG.md after Alex has approved and committed it
disable-model-invocation: true
---

Update CLIVE's status after an approved task. Optional notes: $ARGUMENTS

1. Read `docs/STATUS.md` and the latest commits (`git log -5 --oneline`).
2. Update only what changed: workstream status, "Next task", open risks,
   Simpro access, ADR status. Set "Last updated" to today's date.
3. Add a concise `docs/CHANGELOG.md` entry if the task changed behaviour,
   infrastructure or documentation structure.
   `STATUS.md` owns phase status (since W6 T1); `docs/roadmap.md` links to it
   and is not updated with status.
   For every living document changed (including `STATUS.md` and the
   CHANGELOG), update its "Current state" cell in `docs/README.md` §3 in the
   same commit.
4. Keep `STATUS.md` short: no history, no narrative; history goes in the CHANGELOG.
5. Do not change any ADR status unless Alex has explicitly said it is accepted.
6. Show the diff and propose a commit message (`docs(status): ...`). Stop for approval.
