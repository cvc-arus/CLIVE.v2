---
name: sprint-task
description: Run exactly one task from a CLIVE sprint task file, verify it, and stop for approval. Usage /sprint-task <task-file> <task-id>
disable-model-invocation: true
---

Run ONE task from a CLIVE sprint task file. Arguments: $ARGUMENTS
(first: path to the task file; second: task id, e.g. T1).

1. Read the root `CLAUDE.md`, `docs/STATUS.md`, and the task file.
2. Restate the task's objective, the steps you will take, and the files you
   expect to change. If the task is marked [HUMAN], do not perform it: list
   exactly what Alex must do and stop.
3. Check dependencies listed in the task file against `docs/STATUS.md`. If a
   dependency is not met, stop and report.
4. Perform the task. Follow the task's constraints and the root `CLAUDE.md` rules:
   - ask before any destructive action or host-level change;
   - never print or commit secrets;
   - if the task file and the codebase disagree, stop and report instead of guessing.
5. Run the task's verification steps and show the actual output.
6. Report: what changed (files), verification results, anything left
   undone, and a proposed conventional commit message.
7. STOP. Do not commit until Alex approves. Do not start the next task.
