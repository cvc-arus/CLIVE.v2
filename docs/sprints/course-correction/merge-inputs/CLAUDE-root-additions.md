<!--
Merge the section below into the existing root CLAUDE.md (W6 T6).
Do not replace existing content. Flag conflicts rather than resolving them silently.
-->

## Where to find current state

- **Current status:** `docs/STATUS.md`. The only living document that states
  status. Never write status into other documents; link to it instead.
- **Current sprint:** `docs/sprints/course-correction/` (plan:
  `docs/course-correction-plan.md`).
- **Decisions:** `docs/ADR/ADR-index.md` (index). Proposed ADRs are not decisions yet.
- **Historical documents:** listed in `docs/README.md` §6 (`docs/scope/`,
  `docs/phase*/` sprint records, `docs/doc-audit.md`). Read-only; factual errors
  get a dated correction note only when Alex asks.
- **Simpro facts:** `docs/simpro/simpro-api-findings.md`.

## How work is done

- One task per session, run with `/sprint-task <file> <task id>`. After
  verification, report and stop. Never continue to the next task without approval.
- Never commit without Alex's approval. Conventional commit messages.
- After an approved commit, Alex runs `/status-update`.
- New sprints use `docs/templates/sprint-full.md` when they change
  infrastructure, security or data; otherwise `sprint-short.md`. (Conflicts
  with §5 "Plan before code" and `docs/development-standards.md` §8, which
  require the full format; W6 T6 amends both.)
- Tasks marked [HUMAN] are never performed by Claude Code.
- If a task file, document, or ADR disagrees with the code, the code is the
  source of truth: stop and report the discrepancy.

## ADR rules

- Follow the naming convention and numbering rules in `docs/ADR/ADR-index.md`.
- Before creating an ADR, read the index and the `docs/ADR/` folder; the next
  number is the highest existing number + 1. Add the index row in the same commit.
- Drafts arriving from outside the repo use `ADR-XXX`; assign the real number
  only at commit time and update every reference to it.
- Never reuse a number, never rewrite an accepted ADR (write a superseding ADR
  and update only the old one's Status line, per `docs/CLAUDE.md` §4), and
  never change a status to Accepted without Alex.

## Safety rules

- Ask before any destructive action: removing volumes or containers holding
  data, dropping databases, deleting or overwriting backups, `git push --force`,
  rewriting git history.
- Ask before host-level changes: apt packages, systemd units, cron, firewall,
  files outside the repo (except the agreed backup target).
- Never print, log or commit secrets. Refer to `.env` variables by name only.
- Never run tests or scripts against <ENVIRONMENT_TYPE> Simpro. Sandbox tests run
  only when Alex has set sandbox credentials and asked for them, and only once
  Alex has approved an exception to §3 (code and tests must never contact
  `*.simprosuite.com`).

## Architecture rules (from ADRs)

- Simpro Company IDs are configuration. Never assume 1 and 2 outside the mock.
- Simpro data is never written to the pgvector knowledge base (ADR-015, proposed).
- Access control is enforced server-side and deny-by-default; never via prompts (ADR-014, proposed).
- SQLAlchemy stays synchronous unless an ADR says otherwise.
- The rate limiter's budget is per `SimproClient` instance (ADR-010;
  `src/simpro_client/CLAUDE.md` §10), not per process or per Simpro build:
  services calling Simpro run a single worker with one client.
  (The gateway-only import rule is already in §3, from ADR-009.)
- Mock scope is frozen: only add mock behaviour required by an approved task.
