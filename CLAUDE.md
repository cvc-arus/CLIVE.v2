# CLAUDE.md — CLIVE repository (root)

Guidance for Claude Code in this repository. This root file holds project-wide
rules. Directory files add narrower rules and are loaded when you work there:

- `docs/CLAUDE.md` — documentation, ADRs, verification evidence
- `services/simpro_mock/CLAUDE.md` — mock FastAPI service, PostgreSQL, Alembic, Docker
- `src/simpro_client/CLAUDE.md` — `simpro_client` library architecture and rules
- `tests/CLAUDE.md` — test layers, pytest conventions, determinism

The documentation index (`docs/README.md`) lists every document and whether
it is maintained. These files must be named exactly `CLAUDE.md`.

If a directory file and this file seem to conflict, stop and ask. Do not pick one.

## 1. What this project is

CLIVE is a self-hosted enterprise AI platform for CVC (CCTV and security),
run with Docker Compose on one Ubuntu 24.04 host. Alex is the sole developer and
the approver for every sprint and architectural decision.

- Phases 1–2 (complete, rarely touched): Ollama + Open WebUI; RAG via
  PostgreSQL/PGVector + Apache Tika.
- Phase 3 (**closed 2026-10-09**, Alex): Simpro integration. **Live Simpro API
  access arrived 2026-10-16** (OAuth2 Client Credentials on CVC's production
  build; the environment type is in the private build notes). It is used read-only, under the rules in §3 and
  §9; nothing in the code points at it yet.
  - `src/simpro_client/` — reusable, typed, synchronous Python client library.
  - `services/simpro_mock/` — FastAPI + PostgreSQL mock of the Simpro REST API.
  - Both are shaped to Simpro's **published** OpenAPI contract, vendored at
    `docs/contracts/simpro-openapi-v1-get-subset.json` (ADR-013), and
    `tests/test_spec_conformance.py` proves it without API access.
  - Closed does not mean frozen: `docs/known-issues.md` still lists the
    `pip install -e ".[dev]"` pitfall, and the 2026-10-17 live
    smoke check found three differences that break the client
    (`docs/simpro/mock-vs-public-api.md` §6); fixing them is course correction W1.
    (The lint debt carried past the close was cleared on 2026-10-12, PR #47.)
- Phase 4 (not started, **no longer blocked**): document generation. ADR-009's
  decision is recorded, so scoping can begin. Its entry criteria now include
  `clive-gateway`'s query catalogue covering Customers, Sites, Contacts, Jobs,
  Quotes, Projects, Assets and Employees.
- Phases 5–10 (not started): security/reverse proxy, agents, customer
  intelligence, monitoring. See `docs/roadmap.md`.

The client talks to the mock **only over HTTP**. Switching to real Simpro must
be a configuration change (`SIMPRO_BASE_URL`, `SIMPRO_TOKEN_URL`, credentials),
never a client code change.

## 2. Source of truth

1. The code and the results of actually running it are the source of truth.
2. ADRs record intended architecture and binding constraints.
3. PDDs, scope files, roadmap and sprint reports are context and may be stale.

Never treat a component as implemented because a roadmap, ADR, PDD, sprint
report, or earlier CLAUDE.md describes it. Confirm the file exists and read
it. When documents and code disagree, say so explicitly. Do not quietly
"fix" either side to match the other.

Where to find current state:

- **Current status:** `docs/STATUS.md`, the only living document that states
  status. Never write status into other documents; link to it instead.
- **Current sprint:** `docs/sprints/course-correction/` (plan:
  `docs/course-correction-plan.md`).
- **Decisions:** `docs/ADR/ADR-index.md`. Proposed ADRs are not decisions yet.
- **Historical documents:** listed in `docs/README.md` §6 (`docs/scope/`,
  `docs/phase*/` sprint records, `docs/doc-audit.md`). Read-only; factual errors
  get a dated correction note only when Alex asks.
- **Simpro facts:** `docs/simpro/simpro-api-findings.md`.

## 3. Architecture constraints (hard rules)

- **Synchronous throughout.** Sync `httpx.Client`; sync SQLAlchemy 2.0 with
  `psycopg2-binary`. Do not introduce async SQLAlchemy, `asyncpg`,
  `httpx.AsyncClient`, or an async database layer without a new ADR.
- **Package independence.** `simpro_client` must never import `simpro_mock`,
  and `simpro_mock` must never import `simpro_client`. They are separate
  projects with separate `pyproject.toml` / `uv.lock` files.
- **Library-first, behind one gateway (ADR-006, amended by ADR-009).**
  `simpro_client` stays an importable package with no CLIVE specifics in it.
  ADR-009's decision (recorded 2026-10-09) is that exactly **one** runtime
  service, `clive-gateway`, imports it; every other consumer reaches Simpro
  through that service's HTTP API. Tests and developer tooling against the mock
  are the only exceptions. **`clive-gateway` does not exist yet** — do not
  create it, stub it, or import `simpro_client` from new code until it is
  scoped and approved (§5, no speculative implementation).
- **Read-only scope.** All typed endpoints and all mock resource routes are
  GET-only (the mock's only POST is `/oauth2/token`). Do not add write
  operations without an approved scope change.
- **Live Simpro is read-only (Alex, 2026-10-16).** CLIVE works against CVC's live
  Simpro build; the environment type is in the private build notes. The only requests allowed to
  `*.simprosuite.com` are `GET`s and the OAuth2 token `POST`. Nothing is ever
  written to Simpro: no `POST`, `PUT`, `PATCH` or `DELETE` on any resource,
  whatever an endpoint or task appears to need. The API application has <APP_PERMISSION_LEVEL>
  rights in Simpro (no dedicated read-only security group), so this rule and the
  GET-only client are the only guard against writes.
- **Two isolated Postgres instances.** `postgres` (port 5432, Phase 2
  PGVector knowledge base) must never be used by Phase 3 code or tests, with
  one exception (ADR-014; resolved by Alex 2026-10-15): `clive-gateway` keeps
  its own data in a dedicated `clive_gateway` database on this instance,
  through its own least-privilege DB user. It must never connect to the
  knowledge-base database, and no test may run against port 5432.
  `simpro-mock-db` (port 5433) is the only database for the mock and Phase 3
  tests.
- **No architectural change without an ADR** (new service, new dependency
  category, async, auth flow, handoff mechanism, persistence strategy).
- **Self-hosted.** No cloud AI providers or external SaaS calls unless Alex
  explicitly approves. CVC's own Simpro build (`*.simprosuite.com`) is the one
  approved external API, read-only as above.
- **Simpro company IDs are configuration.** CVC's are Service <company-id> and Projects
  <company-id> (Alex, 2026-10-16). **Only <company-id> and <company-id> are ever used** (Alex, 2026-10-17): the
  build also has companies <company-id> and <company-id>, which CLIVE does not use. Listing
  `/companies/` (which returns them) is allowed, but no request is ever sent
  to a route scoped to company <company-id> or <company-id>, and they are never included in
  CLIVE's results. Never assume 1 and 2 outside the mock.
- **Rate limiter budget is per `SimproClient` instance** (ADR-010;
  `src/simpro_client/CLAUDE.md` §10), not per process or per Simpro build.
  Services calling Simpro run a single worker with one client.
- **Mock scope is frozen.** Only add mock behaviour required by an approved task.
- From Proposed ADRs (not yet decisions, but no code may contradict them
  until Alex decides): Simpro data is never written to the pgvector knowledge
  base (ADR-015); access control is enforced server-side and deny-by-default,
  never via prompts (ADR-014).

## 4. ADR status (snapshot; re-verify before relying on this)

| ADR | Topic | Status |
|---|---|---|
| 001–003 | Local LLM stack, PGVector, Tika | Accepted, implemented |
| mock | `adr-mock-simpro-api.md` | Accepted, but its "Capabilities & Coverage" list is **superseded by ADR-013**: the route count predates the 12-resource mock, and the payload-fidelity claim is contradicted by Simpro's published spec |
| 004 | httpx | Accepted, implemented |
| 005 | Client Credentials + API key fallback; Authorization Code deferred | Accepted, implemented |
| 006 | Library-first `simpro_client` | Accepted, implemented. **"No service wrapper" partially superseded by ADR-009**; the library-first part stands |
| 007 | pydantic-settings, `SIMPRO_` / `SIMPRO_MOCK_` prefixes | Accepted, implemented |
| 008 | Rate limiting | Withdrawn 2026-09-29 as a duplicate of ADR-010; kept for history |
| 009 | Phase 3 → 4 handoff | **Decision recorded 2026-10-09 (Alex): Option B**, a single `clive-gateway` service imports `simpro_client` and serves every other consumer over HTTP. **Accepted** (Status and `Related:` lines updated by Alex 2026-10-15). `clive-gateway` **does not exist yet** — do not build it unasked |
| 010 | Resilience: token bucket, 401/429 budgets, error hierarchy | Approved; implemented with deviations (see `src/simpro_client/CLAUDE.md`). §2.5 superseded by ADR-011 |
| 011 | Exception hierarchy and `SimproAuthError` context (supersedes ADR-010 §2.5) | Accepted 2026-10-06, implemented |
| 012 | Retry delay ceiling (`SIMPRO_MAX_RETRY_DELAY`) and token-refresh concurrency | Accepted 2026-10-06 (supersedes ADR-010 §2.3, extends §2.1) |
| 013 | Re-shape mock and client to Simpro's published OpenAPI spec | Accepted 2026-10-07, **implemented 2026-10-08** (all 7 sprints). **All 50 conformance checks pass and `tests/spec_conformance_baseline.json` is empty**, so every client model validates payloads generated from Simpro's published contract. Field names, types and optionality are governed by `docs/contracts/simpro-openapi-v1-get-subset.json`. The mock honours `columns` on all 25 routes, `orderby` and `limit` on all 13 collection routes, and returns a 400 on an unknown filter or an unorderable `orderby` field. "`ID` is always included" in §5 is superseded by ADR-016 |
| 014 | Simpro data access control model | **Proposed** 2026-10-09. Stores `clive_gateway` on the Phase 2 Postgres; the §3 conflict was resolved by Alex on 2026-10-15 with a narrow exception in §3 |
| 015 | Conversational access approach (tool calling over a fixed query catalogue) | **Proposed** 2026-10-09 |
| 016 | `columns` projections: server adds nothing, client asks for the model's required fields (supersedes "`ID` is always included" in ADR-013 §5) | **Accepted** 2026-10-19 (Alex), implemented |

Re-verify this table before relying on it; it is a snapshot.

ADR rules:

- Follow the naming convention and numbering rules in `docs/ADR/ADR-index.md`.
- Before creating an ADR, read the index and the `docs/ADR/` folder; the next
  number is the highest existing number + 1. Add the index row in the same commit.
- Drafts arriving from outside the repo use `ADR-XXX`; assign the real number
  only at commit time and update every reference to it.
- Never reuse a number, never rewrite an accepted ADR (write a superseding ADR
  and update only the old one's Status line, per `docs/CLAUDE.md` §4), and
  never change a status to Accepted without Alex.

## 5. How to work

- **Plan before code.** For sprint work, produce the plan in the project's
  sprint format and wait for Alex's approval. Sprints that change
  infrastructure, security or data use the full 14-section format
  (`docs/templates/sprint-full.md`: Goal, Business value, Tasks,
  Implementation, Commands, Configuration, Folder structure, Files created,
  Verification, Rollback, Common issues, Documentation updates, Git commit,
  Acceptance criteria). Other sprints may use `docs/templates/sprint-short.md`
  (Goal, Tasks, Verification, Rollback, Git commit, Acceptance criteria). If in
  doubt, use the full format. See `docs/development-standards.md` §8.
- One sprint and one task at a time. Do not start the next until Alex confirms.
- Sprint tasks run with `/sprint-task <file> <task id>`, one task per
  session: after verification, report and stop. After an approved commit, Alex
  runs `/status-update`.
- Tasks marked **[HUMAN]** are never performed by Claude Code; list what Alex
  must do and stop.
- If a task file, document or ADR disagrees with the code, the code is the
  source of truth: stop and report the discrepancy.
- Explain why before how, and state trade-offs when proposing a change.
- Prefer targeted, minimal changes over rewrites. Do not refactor, reformat,
  or "tidy" code outside the task's scope.
- If the requested approach seems worse than an alternative, say so and
  explain before doing anything different.

### No speculative implementation

- Do not create stubs, placeholders, or empty modules for planned features.
- Do not add configuration, abstractions, or extension points "for later".
- Do not reference files, functions, settings, markers, or commands you have
  not confirmed exist.
- If a task seems to need something that does not exist, stop and report it.

## 6. Commands (verified to exist)

Root project (`simpro_client`), from the repo root, using `uv`:

```bash
uv sync                                  # installs dev group (PEP 735)
uv run pytest -q -m "not integration"    # offline suite
uv run pytest tests/test_client.py::test_successful_get -v
uv run ruff check <paths>                # check only; see §7
uv run ruff format --check <paths>
```

- `pip install -e ".[dev]"` does **not** install dev tools; dev dependencies
  live in `[dependency-groups]`. Use `uv sync`.
- Env vars go before `uv run`: `VAR=x uv run cmd`, not `uv run VAR=x cmd`.

Mock and full stack: see `services/simpro_mock/CLAUDE.md`. Test layers:
`tests/CLAUDE.md`.

## 7. Coding standards

- Python 3.12 (pinned 3.12.3 on the host), PEP 8, ruff (`line-length = 88`,
  rules `E F I N W UP B A SIM`, configured in root `pyproject.toml`).
- Type hints and docstrings on all new or modified public functions and
  classes. Do not remove existing type hints or docstrings.
- `str | None` union syntax, not `Optional[...]`.
- Structured logging via `simpro_client.logging`; no `print` in library code.
- Configuration through pydantic-settings and environment variables only.
- Exact-pinned dependencies (`==`). Adding any runtime dependency needs a
  stated justification; adding a new category of dependency needs an ADR.

**Lint baseline** (re-verified 2026-10-15; re-verify before relying on this):
`uv run ruff check .` and `uv run ruff format --check .` pass on the whole
repository, including Python code blocks in Markdown. The earlier debt was
cleared on 2026-10-12 (PR #47). Therefore:

- New and modified files must pass `ruff check` and `ruff format --check`;
  the whole-repo commands must keep passing.
- Intentional exceptions are per-file ignores in the root `pyproject.toml`
  (`B008`/`N803` in the mock's `routers.py`; see `services/simpro_mock/CLAUDE.md`
  §4). Add a new one only with a stated reason.
- Do not run `ruff --fix` or `ruff format` on files outside your change.
- If a check fails on code you did not touch, report it; do not silently fix
  it in unrelated work.

## 8. Git

- Work on `develop`; `main` is updated via pull request.
- Branch names are `<type>/<kebab-case-topic>`, branched from an up-to-date
  `develop`, where `<type>` is the same word the commit message would use
  (`feat`, `fix`, `docs`, `chore`, `refactor`). Examples from history:
  `fix/auth-error-context`, `docs/accept-adr-011`, `fix/mock-reproducibility`.
  The older `feat-pagination-and-retries` uses a dash instead of a slash; it
  is the one exception and not the pattern to copy. If Alex gives a branch
  name, use it exactly; otherwise propose one in this form and wait.
- Never push without Alex's explicit approval (`.claude/settings.json` asks on
  `git push`). If history must be rewritten, use `--force-with-lease`, never
  `--force`, and only when asked.
- Commit only when Alex asks. At the end of a sprint, propose the commit
  message and wait. One logical change per commit, with a descriptive
  conventional commit message (`type(scope): summary`; existing history uses
  `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- Never commit `.env`, `.venv/`, `__pycache__/`, `*.egg-info/`, `backups/`,
  or coverage output. Some bytecode and `egg-info` files are still tracked
  (re-verify before relying on this), so running tests can make them appear
  modified. Restore them with `git checkout -- <path>`; never stage them.
- A sprint is complete only after its documentation update and commit.

## 9. Security

- Never read, print, edit, or summarise `.env` or `.env.*` (denied in
  `.claude/settings.json`). Use `.env.example` to learn variable names.
- Never hardcode secrets or log tokens, client secrets, or API keys.
- Never print, log or commit secrets. Refer to `.env` variables by name only.
- The mock's static bearer token (a default in its `config.py`) is
  development-only. Do not copy that pattern into new services or into
  `simpro_client`. Mock DB credentials come from `.env`
  (`SIMPRO_MOCK_DB_*`).
- New ports bind to `127.0.0.1` unless there is a stated reason not to.
  Keep exposed ports to a minimum.
- Least privilege: Phase 3 is read-only against Simpro.
- Ask before any destructive action: removing volumes or containers holding
  data, dropping databases, deleting or overwriting backups, `git push --force`,
  rewriting git history.
- Ask before host-level changes: apt packages, systemd units, cron, firewall,
  files outside the repo (except the agreed backup target).
- **No CVC client data reaches Claude Code (Alex, 2026-10-16).** Anything a
  command prints lands in the conversation, so code that reads live Simpro
  data or knowledge-base content prints only status codes, counts, field
  names, header names and pass/fail, never values. Watch for indirect leaks:
  pytest and Pydantic failure output echoes input values (run with
  `--tb=no`), as do log lines and error bodies. When values must be looked
  at, give Alex the command to run and ask for a summary.
- Requests to live Simpro (GET only, §3) run only when Alex asks for them. The
  default test suite never contacts Simpro; any live test must be opt-in and
  skipped by default.

## 10. Reporting results

- Report what you actually ran and its actual output (test counts, lint
  results, commit hash). Never claim a check passed without running it.
- If you could not run something (for example, Docker is unavailable, so
  integration tests could not run), say so plainly.
- List every file you changed.
