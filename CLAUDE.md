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
- Phase 3 (**closed 2026-10-09**, Alex): Simpro integration. **There is still no
  live Simpro API access.**
  - `src/simpro_client/` — reusable, typed, synchronous Python client library.
  - `services/simpro_mock/` — FastAPI + PostgreSQL mock of the Simpro REST API.
  - Both are shaped to Simpro's **published** OpenAPI contract, vendored at
    `docs/contracts/simpro-openapi-v1-get-subset.json` (ADR-013), and
    `tests/test_spec_conformance.py` proves it without API access.
  - Closed does not mean frozen: `docs/known-issues.md` still lists the
    `pip install -e ".[dev]"` pitfall and the pre-existing lint debt, and four
    mock behaviours remain unverifiable without live credentials.
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
- **Two isolated Postgres instances.** `postgres` (port 5432, Phase 2
  PGVector knowledge base) must never be used by Phase 3 code or tests.
  `simpro-mock-db` (port 5433) is the only database for Phase 3.
- **No architectural change without an ADR** (new service, new dependency
  category, async, auth flow, handoff mechanism, persistence strategy).
- **Self-hosted.** No cloud AI providers or external SaaS calls unless Alex
  explicitly approves. Code and tests must never contact `*.simprosuite.com`.

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
| 009 | Phase 3 → 4 handoff | **Decision recorded 2026-10-09 (Alex): Option B**, a single `clive-gateway` service imports `simpro_client` and serves every other consumer over HTTP. Its Status line still reads Proposed and its `Related:` line miscites ADR-011, both pending Alex. `clive-gateway` **does not exist yet** — do not build it unasked |
| 010 | Resilience: token bucket, 401/429 budgets, error hierarchy | Approved; implemented with deviations (see `src/simpro_client/CLAUDE.md`). §2.5 superseded by ADR-011 |
| 011 | Exception hierarchy and `SimproAuthError` context (supersedes ADR-010 §2.5) | Accepted 2026-10-06, implemented |
| 012 | Retry delay ceiling (`SIMPRO_MAX_RETRY_DELAY`) and token-refresh concurrency | Accepted 2026-10-06 (supersedes ADR-010 §2.3, extends §2.1) |
| 013 | Re-shape mock and client to Simpro's published OpenAPI spec | Accepted 2026-10-07, **implemented 2026-10-08** (all 7 sprints). **All 50 conformance checks pass and `tests/spec_conformance_baseline.json` is empty**, so every client model validates payloads generated from Simpro's published contract. Field names, types and optionality are governed by `docs/contracts/simpro-openapi-v1-get-subset.json`. The mock honours `columns` on all 25 routes, `orderby` and `limit` on all 13 collection routes, and returns a 400 on an unknown filter or an unorderable `orderby` field |

Re-verify this table before relying on it; it is a snapshot.

## 5. How to work

- **Plan before code.** For sprint work, produce the plan in the project's
  sprint format (Goal, Business value, Tasks, Implementation, Commands,
  Configuration, Folder structure, Files created, Verification, Rollback,
  Common issues, Documentation updates, Git commit, Acceptance criteria;
  see `docs/development-standards.md` §8). Wait for Alex's approval.
- One sprint and one task at a time. Do not start the next until Alex confirms.
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

**Lint baseline** (re-verify before relying on this): `ruff check .` and
`ruff format --check .` do not pass (existing debt in `src/`, `tests/`,
`services/`, `scripts/`, and Markdown code blocks). Therefore:

- New files must pass `ruff check` and `ruff format --check`.
- Modified files must not gain new violations. Code you add or rewrite must
  be clean. Pre-existing violations elsewhere in the file are reported, not
  fixed, unless the task asks for it. (Some are intentional; see
  `services/simpro_mock/CLAUDE.md` §4 for `B008`/`N803` in `routers.py`.)
- Do not run `ruff --fix` or `ruff format` on files outside your change.
- Report pre-existing lint failures; do not silently fix them in unrelated work.

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
  message (existing history uses `feat:`, `fix:`, `chore:`, `refactor:`).
- Never commit `.env`, `.venv/`, `__pycache__/`, `*.egg-info/`, `backups/`,
  or coverage output. Some bytecode and `egg-info` files are still tracked
  (re-verify before relying on this), so running tests can make them appear
  modified. Restore them with `git checkout -- <path>`; never stage them.
- A sprint is complete only after its documentation update and commit.

## 9. Security

- Never read, print, edit, or summarise `.env` or `.env.*` (denied in
  `.claude/settings.json`). Use `.env.example` to learn variable names.
- Never hardcode secrets or log tokens, client secrets, or API keys.
- The mock's static bearer token (a default in its `config.py`) is
  development-only. Do not copy that pattern into new services or into
  `simpro_client`. Mock DB credentials come from `.env`
  (`SIMPRO_MOCK_DB_*`).
- New ports bind to `127.0.0.1` unless there is a stated reason not to.
  Keep exposed ports to a minimum.
- Least privilege: Phase 3 is read-only against Simpro.

## 10. Reporting results

- Report what you actually ran and its actual output (test counts, lint
  results, commit hash). Never claim a check passed without running it.
- If you could not run something (for example, Docker is unavailable, so
  integration tests could not run), say so plainly.
- List every file you changed.
