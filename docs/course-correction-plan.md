# CLIVE — Course Correction Plan (v2)

| | |
|---|---|
| **Date** | 2026-10-12 |
| **Owner** | Alex |
| **Status** | Approved |
| **Supersedes** | Course Correction Plan v1 (same date) |
| **Execution** | Claude Code, one task at a time, using the task files in `docs/sprints/course-correction/` |

## 1. Purpose

The October 2026 architecture review found CLIVE technically on track but
sequenced by component rather than by business value. This two-week sprint
fixes the highest risks, consolidates documentation, and gathers the evidence
needed to choose the next phase order.

## 2. What changed since v1

| Change | Effect on the plan |
|---|---|
| Phase 3 confirmed finished | W6 records the sign-off instead of investigating status |
| Simpro: API access required, price and access level awaited | W1 now tracks the commercial answer rather than asking for a decision |
| Simpro: free **shared sandbox** available via a Support case | W1 raises the case immediately. The sandbox lets `simpro_client` and Phase 3B be validated against the real API before production access. Biggest change in this revision. |
| Simpro: API credentials operate within **Security Group** boundaries | A dedicated read-only security group for CLIVE becomes the outer limit of what CLIVE can ever see. ADR-015 amended. |
| Simpro: public API documentation available | W1 compares the mock against the published API |
| Simpro: real Company IDs come from the build's setup | Company IDs must be configuration, never assumed to be 1 and 2 |
| Simpro: webhooks for job and quote events | Recorded for a future sync/caching ADR; not in scope |
| Backup target: `/` (`/dev/sda2`) proposed | W5 must confirm which disk holds CLIVE data; a backup on the same disk does not protect against disk failure |
| Lighter sprint template approved | Templates added to `docs/templates/` |
| Development is done with Claude Code | Each workstream is a task file Claude Code can execute; `CLAUDE.md` and two project skills govern how |

Full Simpro detail: `docs/simpro/simpro-api-findings.md`.

## 3. Workstreams

| # | Workstream | Template | Who | Effort |
|---|---|---|---|---|
| W1 | Simpro access and sandbox | Short | Alex (support cases) + Claude Code (mock comparison) | 1–2 days, then waiting |
| W2 | Document generation value check | Short | Alex | ~2 days, spread out |
| W3 | Knowledge base audit | Short | Claude Code + Alex | 2–3 days |
| W4 | Evaluation set and baseline | Short | Alex (questions) + Claude Code (runner) | 2–3 days |
| W5 | Backups and restore drill | **Full** (changes data and host) | Claude Code + Alex | 2–3 days |
| W6 | Documentation consolidation and Phase 3 sign-off | Short | Claude Code | 3–4 days |

Task files: `docs/sprints/course-correction/W1-…md` to `W6-…md`.

## 4. Order of work

| Days | Work |
|---|---|
| 1 | W1 human tasks: raise Simpro Support cases (sandbox first) · W6 task 1: record Phase 3 sign-off and create `STATUS.md` |
| 2–3 | W5 backups and restore drill |
| 4–5 | W6 remaining tasks · W1 mock-vs-public-API comparison |
| 6–7 | W3 knowledge base audit |
| 8–9 | W4 evaluation set and baseline |
| 6–10 (alongside) | W2 interviews |
| 10 | Decision point |

Backups first: highest risk, quickest win. W6 task 1 first on day 1 because
every later task updates `STATUS.md`.

## 5. Working with Claude Code

- Root `CLAUDE.md` points Claude Code at `docs/STATUS.md`, the ADR index and the
  current sprint folder.
- Run one task per session: `/sprint-task <task file> <task id>`. Claude Code
  restates the task, does it, runs the verification, reports, proposes a commit
  message, and **stops**.
- Alex reviews, approves the commit, then runs `/status-update`.
- Tasks marked **[HUMAN]** are not executed by Claude Code; it stops and lists
  what Alex must do.
- Destructive operations (deleting volumes, dropping databases, overwriting
  backups, `git push --force`) always require explicit approval in the session.

## 6. Decision point (end of sprint)

Inputs: W1 (commercial answer, sandbox access, mock discrepancies), W2 (value
ranking), W3 (knowledge base gaps), W4 (baseline quality).

| Scenario | Next phase order |
|---|---|
| Sandbox available; Simpro Q&A ranks highest | 3B (built against mock, validated on sandbox) → 4A → 4B |
| Sandbox delayed; RAMS/template documents rank highly | 4A → 3B → 4B |
| Knowledge base audit finds major gaps | Phase 2B (knowledge base remediation) first; 4A depends on it |
| <ENVIRONMENT_TYPE> API access refused | 4A; 3B and 4B paused; mock and sandbox work frozen |

The decision is recorded in `docs/STATUS.md` and, if architectural, in an ADR.

## 7. Changes to existing plans

- **Phase 3B PDD:** testing strategy adds sandbox contract tests; Company IDs
  configurable; Simpro custom fields included in field classification; the
  Simpro security group is the outer permission boundary; model spike uses the
  W4 evaluation set; entry criteria add "course correction sprint complete".
- **ADR-015:** CLIVE roles operate inside a dedicated read-only Simpro security
  group. Option 2 (per-user login) is more viable than assumed, since Simpro
  enforces security groups per user; revisit once the sandbox allows it to be verified.
- **Phase 4:** split into 4A and 4B if W2 supports it.
- **Phase 10:** backup and restore moved into W5; monitoring stays.

## 8. Open items

| Item | Owner | Status |
|---|---|---|
| Simpro price and access level | Simpro representative | Awaited |
| Simpro Support cases (sandbox, OpenAPI export, cross-company credentials, read-only scoping) | Alex | To raise on day 1 |
| Off-machine backup target (NAS or external drive) | Alex / CVC | **Not yet agreed.** Until it exists, backups are cross-disk only and this is recorded as an accepted risk. |
