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
- Phase 3 (active): Simpro integration. **There is no live Simpro API access.**
  - `src/simpro_client/` — reusable, typed, synchronous Python client library.
  - `services/simpro_mock/` — FastAPI + PostgreSQL mock of the Simpro REST API.
- Phase 4+ (not started): document generation, agents, etc. Blocked on ADR-009.

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
- **Library-first (ADR-006).** No service wrapper around `simpro_client`.
  Whether Phase 4 imports it directly or via a wrapper is ADR-009, which is
  **open**. Do not build toward either option.
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

## 4. ADR status (verified against code at commit `31936f8`)

| ADR | Topic | Status |
|---|---|---|
| 001–003 | Local LLM stack, PGVector, Tika | Accepted, implemented |
| mock | `adr-mock-simpro-api.md` | Accepted. Its capability list (4 resources) predates the 12-resource mock |
| 004 | httpx | Accepted, implemented |
| 005 | Client Credentials + API key fallback; Authorization Code deferred | Accepted, implemented |
| 006 | Library-first `simpro_client` | Accepted, implemented |
| 007 | pydantic-settings, `SIMPRO_` / `SIMPRO_MOCK_` prefixes | Accepted, implemented |
| 008 | Rate limiting | **Unresolved:** file text duplicates ADR-010; `ADR-index.md` lists it as Proposed |
| 009 | Phase 3 → 4 handoff | **Open. Do not decide or assume.** |
| 010 | Resilience: token bucket, 401/429 budgets, error hierarchy | Approved; implemented with deviations (see `src/simpro_client/CLAUDE.md`) |

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

**Lint baseline:** at `31936f8`, `ruff check .` and `ruff format --check .`
do not pass (existing debt in `src/`, `tests/`, `services/`, `scripts/`,
and Markdown code blocks). Therefore:

- New files must pass `ruff check` and `ruff format --check`.
- Modified files must not gain new violations. Code you add or rewrite must
  be clean. Pre-existing violations elsewhere in the file are reported, not
  fixed, unless the task asks for it. (Some are intentional; see
  `services/simpro_mock/CLAUDE.md` §4 for `B008`/`N803` in `routers.py`.)
- Do not run `ruff --fix` or `ruff format` on files outside your change.
- Report pre-existing lint failures; do not silently fix them in unrelated work.

## 8. Git

- Work on `develop`; `main` is updated via pull request.
- Never push without Alex's explicit approval (`.claude/settings.json` asks on
  `git push`). If history must be rewritten, use `--force-with-lease`, never
  `--force`, and only when asked.
- Commit only when Alex asks. At the end of a sprint, propose the commit
  message and wait. One logical change per commit, with a descriptive
  message (existing history uses `feat:`, `fix:`, `chore:`, `refactor:`).
- Never commit `.env`, `.venv/`, `__pycache__/`, `*.egg-info/`, `backups/`,
  or coverage output. Some bytecode and `egg-info` files are still tracked at
  `31936f8`, so running tests can make them appear modified. Restore them
  with `git checkout -- <path>`; never stage them.
- A sprint is complete only after its documentation update and commit.

## 9. Security

- Never read, print, edit, or summarise `.env` or `.env.*` (denied in
  `.claude/settings.json`). Use `.env.example` to learn variable names.
- Never hardcode secrets or log tokens, client secrets, or API keys.
- The mock's static bearer token and the mock DB credentials in
  `docker-compose.yml` are development-only. Do not copy that pattern into
  new services or into `simpro_client`.
- New ports bind to `127.0.0.1` unless there is a stated reason not to.
  Keep exposed ports to a minimum.
- Least privilege: Phase 3 is read-only against Simpro.

## 10. Reporting results

- Report what you actually ran and its actual output (test counts, lint
  results, commit hash). Never claim a check passed without running it.
- If you could not run something (for example, Docker is unavailable, so
  integration tests could not run), say so plainly.
- List every file you changed.
