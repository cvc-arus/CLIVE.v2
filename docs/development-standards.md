# CLIVE Development Standards (As Applied in Phase 3)

Consolidates the standards declared in `Clive_Scope.txt` / `__CLIVE_Enterprise_AI_Platform.txt` with how they are actually applied in the current codebase.

## 1. Python

| Standard | Enforcement |
|---|---|
| PEP8 | `ruff` (`select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM"]`) |
| Formatting | `ruff format` / `black` |
| Type hints | Used throughout (`str \| None` union syntax, not `Optional[]`) |
| Docstrings | Present on all public classes/functions in `simpro_client` and `simpro_mock` |
| Line length | 88 (`[tool.ruff] line-length = 88`) |
| Target version | `py312` |
| Logging | Structured JSON via stdlib `logging` + custom `JSONFormatter`, not print statements |
| Configuration | `pydantic-settings`, `.env`-driven, never hardcoded secrets |
| Error handling | Typed exception hierarchies per package (`simpro_client.exceptions`) |

Run locally:
```bash
ruff check src/ --fix
ruff format src/
```

## 2. Testing

- **Framework:** `pytest`, with `respx` for mocking `httpx` traffic in `simpro_client` tests.
- **No live dependency in unit tests:** all 18 tests in `tests/test_auth.py`, `test_client.py`, `test_config.py`, `test_logging.py` run fully offline.
- **Live/integration tests are explicitly separated and skip-gated:** `tests/test_simpro_mock_v2.py` checks reachability of `http://localhost:8100/health` first and applies `pytest.mark.skipif` so the suite never fails just because the mock isn't running.
- **Manual diagnostic scripts are kept outside `tests/`:** `scripts/verify-simpro-mock.py` deliberately lives outside the `tests/` directory and is documented as "not a pytest test," specifically because its helper functions are named `test_list_endpoint`, `test_single_endpoint`, etc., which pytest would otherwise try to collect and run.
- **Anti-pattern to avoid going forward:** `tests/test_simpro_mock.py` (the original script-style file with module-level `assert`s) is still present in the tree even though its replacement (`test_simpro_mock_v2.py`) exists. This should be deleted — see `docs/known-issues.md`.
- **Run tests, don't just read code:** codebase reviews in this project run `pytest tests/ -v` rather than relying on static inspection, since that's what actually surfaces pytest-collection bugs.

Run locally:
```bash
pytest tests/ -v                      # unit tests (offline)
docker compose up -d simpro-mock      # start the mock
python scripts/verify-simpro-mock.py  # manual diagnostic
pytest tests/test_simpro_mock_v2.py -v  # skip-gated integration test
```

## 3. Docker

- Every service runs in Docker; no direct host installation except the dev virtualenv for running `simpro_client`'s own test suite.
- `docker-compose.yml` at repo root; `services/simpro_mock/Dockerfile` for the mock's own image.
- Restart policy `unless-stopped` on every service.
- Persistent state via bind mounts (Phase 1/2 services) or named volumes (`simpro-mock-db-data`).
- Health checks (`pg_isready`) gate service startup ordering via `depends_on: condition: service_healthy`.
- **Editing files on disk is not enough for `simpro-mock`:** its `Dockerfile` bakes `simpro_mock/` source into the image at build time (`COPY simpro_mock/ simpro_mock/`). After any source edit, `docker compose build simpro-mock` (or `docker compose up -d --build simpro-mock`) is required — a plain restart serves stale code.
- Database migrations run automatically on container start (`alembic upgrade head`) before the seed script and `uvicorn` in the mock's `CMD`.

## 4. Configuration & Secrets

- All Simpro-related settings load from `.env` with the `SIMPRO_` prefix (client) or `SIMPRO_MOCK_` prefix (mock service), via `pydantic-settings`.
- `extra="ignore"` on `SimproSettings` lets Simpro keys coexist in the same root `.env` as unrelated PGVector/Postgres credentials without validation errors.
- `.env.example` documents every required key without values; `.env` itself is gitignored.
- No secrets are committed. The mock's static bearer token is a development convenience, not a production credential.

## 5. Package & Dependency Management

- `uv` is the package manager. **Argument order matters:** `ENV_VAR="..." uv run command` works; `uv run ENV_VAR="..." command` fails because `uv` tries to execute the env-var string as a binary.
- `simpro_client` (root `pyproject.toml`): `httpx==0.28.1`, `pydantic==2.13.4`, `pydantic-settings==2.14.2`, `python-dotenv==1.1.0`; dev group: `pytest==9.1.1`, `respx==0.23.1`, `ruff==0.16.1`, `pytest-cov==7.0.0`.
- `simpro_mock` (`services/simpro_mock/pyproject.toml`): `fastapi==0.141.1`, `uvicorn==0.52.4`, `sqlalchemy==2.0.52`, `psycopg2-binary==2.9.12`, `alembic==1.19.1`, `pydantic-settings==2.15.0`, `python-multipart==0.0.27`.

## 6. Database (SQLAlchemy)

- **Synchronous SQLAlchemy 2.0 throughout** (`Mapped[]` / `mapped_column`, `sessionmaker`, `psycopg2-binary` driver) — this is a deliberate, standing decision. Do not introduce `asyncpg` or async sessions without a dedicated ADR, since it would create a sync/async mismatch across the codebase.
- Every relationship declares `back_populates` on both sides (normalized during Sprint 3 review).
- Foreign keys use `ondelete="CASCADE"` for strict ownership (e.g. `Customer.company_id`) and `ondelete="SET NULL"` for optional links (e.g. `Quote.customer_id`, `Project.site_id`).
- Schema changes go through Alembic migrations (`alembic revision` → `alembic upgrade head`), not manual `CREATE TABLE`.

## 7. Git

- Work happens on `develop`; force-pushes use `git push --force-with-lease`, never a plain `--force`, when history is rewritten (this project's `.venv/` accidental-commit cleanup is the precedent).
- Every sprint ends with a git commit and a documentation update, per the project's own sprint template (see `docs/development-standards.md` §8 for the template itself, reproduced from `Clive_Scope.txt`).

## 8. Sprint / Task Template

Every sprint plan and every task within it follows this structure, per the project's founding scope document:

1. Goal
2. Business value
3. Tasks
4. Implementation
5. Commands
6. Configuration
7. Folder structure
8. Files created
9. Verification
10. Rollback procedure
11. Common issues
12. Documentation updates
13. Git commit
14. Acceptance criteria

Work proceeds one sprint at a time; the next sprint does not start until the current one is confirmed complete.

## 9. Documentation Principle

**Code is the sole source of truth.** Project documentation (this file included) is generated from the actual codebase — by reading source, running the test suite, and inspecting the running containers — not from planning transcripts or prior chat summaries. This avoids drift between what the docs claim and what the code actually does. Where a planning document (e.g. `RevisedScope.txt`) and the code disagree, the code wins, and the discrepancy should be called out explicitly rather than silently reconciled in the doc's favor.
