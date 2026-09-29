# CLAUDE.md — `services/simpro_mock/`

Complements the root `CLAUDE.md`. `services/simpro_mock/` is a FastAPI +
PostgreSQL mock of the Simpro REST API, and currently the only service under
`services/`.

## 1. Purpose and fidelity

The mock exists so `simpro_client` can be built and tested without live
Simpro access. Its job is to behave like real Simpro, so the client needs no
code changes when `SIMPRO_BASE_URL` / `SIMPRO_TOKEN_URL` switch to production.

- Match real Simpro's documented behaviour. Do not invent conveniences the
  real API lacks, since the client would come to depend on them.
- It is a separate project: own `pyproject.toml` and `uv.lock`. It must never
  import `simpro_client`.
- Do not add sibling services under `services/` without a stated
  justification and an ADR (root §3). ADR-006 rules out a `simpro_client`
  wrapper service for now, and ADR-009 is open.

## 2. Layout (as implemented)

```
services/simpro_mock/
  Dockerfile, alembic.ini, pyproject.toml, uv.lock, configuration.md
  alembic/env.py, alembic/versions/*.py
  simpro_mock/
    main.py        app + BearerAuthMiddleware + 3 routers
    config.py      Settings, prefix SIMPRO_MOCK_
    database.py    sync engine, SessionLocal, Base, get_db()
    middleware.py  BearerAuthMiddleware, paginate_query, set_pagination_headers
    filtering.py   Simpro-style query filters
    models.py      12 SQLAlchemy ORM models
    schemas.py     PascalCase Pydantic response schemas
    routers.py     health, /oauth2/token, /api/v1.0/... routes
    seed.py        truncate + seed two companies
```

## 3. API contract (what the client depends on)

Any change to these is a breaking change for `simpro_client` and needs a
matching client change, updated tests, and Alex's approval:

- Prefix `/api/v1.0`. `POST /oauth2/token` takes form-encoded client
  credentials and returns `access_token`, `token_type`, `expires_in`.
- All routes except `/health`, `/oauth2/token`, `/docs`, `/openapi.json` and
  `/redoc` require `Authorization: Bearer <SIMPRO_MOCK_MOCK_ACCESS_TOKEN>`.
  Failures return 401 with a JSON `detail`.
- Collection routes end with `/`; detail routes do not.
- 12 resources. Nesting: contacts under customers, assets under sites, notes
  and attachments under jobs. Everything else is under
  `/companies/{company_id}/`.
- Response fields are PascalCase and built explicitly in `routers.py`.
  Schema field names in `schemas.py` are the wire contract.
- List routes accept `page` (≥1, default 1) and `pageSize` (1–250,
  default 30) and set `Result-Total`, `Result-Count`, `Result-Pages`.
  `pageSize` is camelCase on purpose. Do not rename it to satisfy ruff `N803`.
- Missing records raise `HTTPException(404)`.
- GET only (plus the token POST). Do not add write routes without a scope
  change.

When you change a response schema, also update the client model in
`src/simpro_client/models/`, `tests/test_models.py`, and, for routes,
`tests/test_route_contract.py`.

Known fidelity gaps (documented in `adr-mock-simpro-api.md` and
`docs/simpro-mock-api-reference.md`, or found in review):
- No rate limiting; the mock never returns 429. Adding 429 simulation
  changes a documented ADR limitation, so update the ADR too.
- `filtering.py`'s `PASCAL_TO_SNAKE` maps only 11 fields. Unmapped filter
  params (e.g. `SiteID`, `Position`) are **silently ignored**.
- `columns`, `orderby`, `limit` are accepted but ignored.
- `JobNote` and `Attachment` responses have no `CompanyID`.
- The mock does not read or log `X-Correlation-ID`.
- The token endpoint accepts any credentials.

## 4. FastAPI conventions (as used)

- Route handlers are plain `def` (sync), with `db: Session = Depends(get_db)`.
  Do not make handlers `async def` while they use the sync session.
- `BaseHTTPMiddleware.dispatch` is `async def` because Starlette requires it.
  Keep database access out of middleware.
- `Depends(...)` / `Query(...)` in defaults is the FastAPI idiom. Ruff `B008`
  on these is expected; do not restructure routes to silence it.
- Build response objects explicitly with PascalCase fields, following the
  existing routes. Serialise dates with `.isoformat()`.
- Company scoping: every company-level query filters on `company_id`.
  Job-nested resources verify that the job belongs to the company.

## 5. Database and SQLAlchemy

- SQLAlchemy **2.0, synchronous**, `psycopg2-binary`, `create_engine` +
  `sessionmaker`. Do not introduce `asyncpg`, `AsyncSession` or
  `create_async_engine` without an ADR.
- ORM models use `Mapped[...]` / `mapped_column`. Relationships declare
  `back_populates` on both sides. FKs use `ondelete="CASCADE"` for ownership
  and `SET NULL` for optional links.
- Queries use the legacy `db.query(...)` API, which is supported in 2.0. Do
  not mass-migrate to `select()` as a side effect of other work.
- The mock uses its own container `simpro-mock-db` (`postgres:16-alpine`,
  host port 5433, database `simpro_mock`, default `public` schema). Never
  point the mock, its migrations or its seed at the Phase 2 `postgres`
  container (port 5432).

## 6. Migrations (Alembic)

- Every schema change is an Alembic migration. No manual DDL, no
  `Base.metadata.create_all()`.
- `alembic/env.py` does **not** import `simpro_mock.models`, so
  `Base.metadata` is empty there and `alembic revision --autogenerate` would
  generate wrong output (it would try to drop all tables). Write migrations
  by hand. Changing `env.py` is a code change that needs approval.
- Each migration must set `down_revision` to the current single head, have a
  working `downgrade()`, and keep one head (`alembic heads`).
- Migrations run from `services/simpro_mock/`. From the host, point them at
  the mapped port:
  `SIMPRO_MOCK_DATABASE_URL=postgresql://<db-user>:<db-password>@localhost:5433/simpro_mock uv run alembic upgrade head`
- Never edit a migration that has already been applied or committed. Add a
  new one.

## 7. Seed data

- The container runs `alembic upgrade head && python -m simpro_mock.seed &&
  uvicorn ...` on **every start**. `seed.py` **truncates every table with
  `RESTART IDENTITY`** and reseeds. Mock data does not survive a restart.
- Deterministic: two companies, `1` = "CVC Service", `2` = "CVC Projects",
  with fixed per-company counts for most resources.
- Not deterministic: `random` is unseeded (assets per site, notes per job,
  names, values), and dates are relative to `date.today()`. Tests must not
  assert exact random values.
- New seeded tables must be added to `truncate_tables()`.

## 8. Docker

- The `Dockerfile` copies source into the image. After editing anything under
  `services/simpro_mock/`, rebuild: `docker compose up -d --build simpro-mock`.
  A plain restart serves stale code.
- Compose: `simpro-mock` is on host port 8100 (container 8000);
  `simpro-mock-db` is on host 5433 with a `pg_isready` healthcheck. Both use
  `restart: unless-stopped`; the DB uses the named volume
  `simpro-mock-db-data`.
- Inside the Compose network the API is `http://simpro-mock:8000`; from the
  host it is `http://localhost:8100`.
- Hardcoded `clive`/`clive` DB credentials in `docker-compose.yml` are a known
  dev-only exception. Do not replicate the pattern.
- Do not modify Phase 1/2 services (`ollama`, `open-webui`, `postgres`,
  `tika`) as part of Phase 3 work.
- Never run `docker compose down -v` or delete volumes without Alex's explicit
  approval. `-v` removes every named volume in the project, not just the
  mock's. (Phase 1/2 data lives in host bind mounts under `/data/`.)

## 9. Verification for mock changes

1. Lint the files you changed: `uv run ruff check <files>` from the repo root
   (root `pyproject.toml` ruff config applies).
2. Rebuild and start: `docker compose up -d --build simpro-mock`.
3. `curl -s localhost:8100/health`.
4. `uv run pytest -m integration -v` and
   `uv run python scripts/verify-simpro-mock.py` (from repo root).
5. Offline client suite still passes: `uv run pytest -q -m "not integration"`.

If Docker is not available, say that steps 2–4 were not run.
