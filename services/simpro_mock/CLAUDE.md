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
- Its dev tools (`pytest`, `httpx`) are an optional extra in
  `[project.optional-dependencies]`, not a PEP 735 group as in the root
  project. Install them from `services/simpro_mock/` with
  `uv sync --extra dev`. They are range-pinned (`>=`), contrary to root §7;
  report this rather than changing it without a task. Ruff is not in this
  extra; lint from the repo root (§9).
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
    models.py      16 SQLAlchemy ORM models/tables
    schemas.py     PascalCase Pydantic response schemas
    serializers.py ORM row -> wire-shaped dict, per resource and leg
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
- **13 served resources, and the routes come from Simpro's published spec**
  (`docs/contracts/simpro-openapi-v1-get-subset.json`, ADR-013) — not from
  what is convenient here. Nesting: contacts under customers, assets under
  sites, notes and attachments under jobs. Everything else is under
  `/companies/{company_id}/`. Three spellings are not the obvious ones:
  attachments live at `.../jobs/{job_id}/attachments/files/`, project status
  codes at `.../setup/statusCodes/projects/`, and there is **no Projects
  route** — upstream, a project is a Job with `Type: "Project"`.
- **Customers are polymorphic and have three routes, not two.**
  `/customers/` lists both kinds with a `Type` discriminator and an `_href`;
  the full record is on `/customers/individuals/{id}` or
  `/customers/companies/{id}`. There is **no `/customers/{id}`**. Each subtype
  detail route is type-scoped and 404s for an id of the other kind.
- A site belongs to **several** customers, through `site_customers`.
  `Site.Customers` and `Customer.Sites` are the same relation.
- Response fields are PascalCase. Schema field names in `schemas.py` are the
  wire contract; `serializers.py` is what produces them (§4).
- **Collection and detail routes return different field sets.** Real Simpro's
  list routes return a narrow projection — companies, employees and project
  status codes return only `ID` and `Name`, attachments only `ID` and
  `Filename` — and the full record comes from the detail route. The
  re-shaped resources now behave this way; the ones still awaiting their wave
  return every modelled field on both legs.
- `Attachment.ID` is a **string**, not an integer (`file-0001` in the seed).
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
- `columns`, `orderby`, `limit` are accepted but ignored. `simpro_client`
  already sends `columns`, so the projection is the next thing owed here;
  until it lands, list routes return every modelled field rather than the
  narrow default projection real Simpro returns.
- `search` is applied, but only as a mode switch: `search=any` joins the
  field filters with OR; anything else (default `all`) joins them with AND
  (`apply_filters()` in `filtering.py`). It is not a free-text search.
- Thin data behind correct shapes, in the re-shaped resources:
  `Customer.Contracts`, `Customer.ResponseTimes`, `Contact.Contact`,
  `Site.STCZone` and `Site.VEECZone` are always `null`; `Customer.Tags`,
  `Customer.PreferredTechs`, `Customer.CustomFields`, `Contact.CustomFields`,
  `Site.PreferredTechs` and `Site.PreferredTechnicians` are always `[]`. Also
  `Attachment.Folder`
  and `Company.DefaultCostCenter` are always `null` (both nullable upstream;
  the mock models neither folders nor cost centres), `JobNote.Attachments` is
  always `[]` (the mock attaches files to jobs, not to notes), and
  `Employee.Zones` holds only that employee's default zone. The shapes match
  the contract; only the data is sparse. Tests must not assert otherwise.
- The mock does not read or log `X-Correlation-ID`.
- The token endpoint accepts any credentials.

## 4. FastAPI conventions (as used)

- Route handlers are plain `def` (sync), with `db: Session = Depends(get_db)`.
  Do not make handlers `async def` while they use the sync session.
- `BaseHTTPMiddleware.dispatch` is `async def` because Starlette requires it.
  Keep database access out of middleware.
- `Depends(...)` / `Query(...)` in defaults is the FastAPI idiom. Ruff `B008`
  on these is expected; do not restructure routes to silence it.
- **Responses are composed in `serializers.py`, not inline in `routers.py`.**
  Each re-shaped resource has a `<resource>_list_dict()` and a
  `<resource>_detail_dict()` that build a PascalCase dict from the ORM row;
  the handler calls one and returns it. Dates are serialised with
  `.isoformat()` there. Handlers must not hand-build response bodies.
  (Resources not yet re-shaped — jobs, quotes, assets — still build theirs
  inline. They move to `serializers.py` in Wave C; do not convert them early.)
- Collection and detail routes return **different projections**, so a
  re-shaped resource has both an `XListResponse` and an `XDetailResponse` in
  `schemas.py`, and both stay on their route's `response_model`. The
  `response_model` is what catches a typo in a serializer, so do not drop it
  when returning a dict.
- The database stores composite values **flat, one column each**; the nested
  wire shape (`Employee.PrimaryContact`, `Company.Address`) is assembled in
  `serializers.py`. Do not add JSON columns to mirror the wire shape.
- A field whose wire name starts with an underscore (`_href`) must be declared
  as `href: str = Field(alias="_href")` — **`alias`, not
  `serialization_alias`**. FastAPI validates the serializer's dict against the
  `response_model` before serialising it, so a serialization-only alias makes
  every such response a 500. A field *named* `_href` would vanish instead,
  because Pydantic treats it as a private attribute.
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
- The mock uses its own Compose service `simpro-mock-db` (container name
  `clive-simpro-mock-db`, so `docker exec` needs that name;
  `postgres:16-alpine`, host port 5433, database from `SIMPRO_MOCK_DB_NAME`, default
  `public` schema). Never point the mock, its migrations or its seed at the Phase 2 `postgres`
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
  `SIMPRO_MOCK_DATABASE_URL=postgresql://<user>:<password>@localhost:5433/<db-name> uv run alembic upgrade head`,
  using the `SIMPRO_MOCK_DB_*` values from `.env` (ask Alex; never read `.env`).
  `database_url` has no default, so it must be set.
- Never edit a migration that has already been applied or committed. Add a
  new one.

## 7. Seed data

- The container runs `alembic upgrade head && python -m simpro_mock.seed &&
  uvicorn ...` on **every start**. `seed.py` **truncates every table with
  `RESTART IDENTITY`** and reseeds. Mock data does not survive a restart.
- Deterministic within a day: two companies, `1` = "CVC Service",
  `2` = "CVC Projects", each with three `zones`. `random` is seeded with `RANDOM_SEED`, the
  re-read queries are ordered by `id`, and timestamps are anchored to
  midnight of `date.today()`, so every restart on the same day yields
  identical data.
- Changes daily: all dates and timestamps are relative to `date.today()`.
  Tests must still not assert exact seeded values.
- `truncate_tables()` is driven off `reversed(Base.metadata.sorted_tables)`,
  so a table added by a migration is picked up automatically. Do not
  reintroduce a hardcoded table list.
- The `projects` table is still seeded but no route serves it; it is
  converted to `Type="Project"` jobs and dropped in ADR-013's Wave C.
- `Attachment.id` is a string and is **assigned explicitly** by the seed
  (`file-0001`, …), not autoincremented. Keep it deterministic.
- Customers alternate `Individual` / `Company` within each company, so both
  subtype routes always have data. Do not make one kind empty.
- `custom_fields` / `custom_field_values` are seeded for **sites** only; jobs
  and assets join in Wave C.

## 8. Docker

- The `Dockerfile` copies source into the image. After editing anything under
  `services/simpro_mock/`, rebuild: `docker compose up -d --build simpro-mock`.
  A plain restart serves stale code.
- The image is two-stage on `python:3.12.3-slim-bookworm` (matches the host
  Python). The build stage runs `uv sync --locked` (uv `0.12.15`) into
  `/opt/venv`, so dependencies come from `uv.lock` exactly, and the build
  fails if `uv.lock` is out of date with `pyproject.toml` (run `uv lock`
  here after changing dependencies). The runtime stage has no uv and runs
  as the non-root user `app` (uid 10001).
- Compose: `simpro-mock` is on host port `127.0.0.1:8100` (container 8000)
  with a Python `urllib` healthcheck on `/health` (the image has no `curl`);
  `simpro-mock-db` is on `127.0.0.1:5433` with a `pg_isready` healthcheck.
  Both use `restart: unless-stopped`; the DB uses the named volume
  `simpro-mock-db-data`.
- Inside the Compose network the API is `http://simpro-mock:8000`; from the
  host it is `http://localhost:8100`.
- Mock DB credentials come from the root `.env` keys `SIMPRO_MOCK_DB_USER`,
  `SIMPRO_MOCK_DB_PASSWORD` and `SIMPRO_MOCK_DB_NAME` (placeholders in
  `.env.example`). Postgres applies them only when the volume is first
  created; changing them means recreating `simpro-mock-db-data`.
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
