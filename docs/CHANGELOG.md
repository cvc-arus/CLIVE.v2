# CLIVE Changelog

Reconstructed from `RevisedScope.txt`, chat history, and the current state of the codebase. Dates reflect the sprint/phase narrative where exact commit dates were not available from the shallow git history at review time.

## Phase 1 — Local AI Platform
- Ubuntu 24.04 LTS development host provisioned
- Docker Compose stack: Ollama + Open WebUI
- Local models pulled (`llama3.2`, `qwen2.5-coder:7b`)

## Phase 2 — Production RAG
- Added `postgres` service (`pgvector/pgvector:0.8.6-pg16`), bound to `127.0.0.1` only
- Added `tika` service (`apache/tika:3.3.1.0-full`) for document extraction
- Configured Open WebUI to use PGVector + Tika + Ollama `nomic-embed-text` embeddings
- Enabled Hybrid Search (BM25 + vector + CrossEncoder reranking)
- Tuned chunking: 1000/100 → 1500/200 (chunk size / overlap)
- Added `scripts/backup.sh` (dump, compress, integrity/restore verification, rotation) and `scripts/verify.sh`

## Phase 3 — Simpro API Integration

### Sprint 1 — Client Foundation
- Created `src/simpro_client/` package (editable install, `pyproject.toml`)
- `config.py`: `SimproSettings` via `pydantic-settings`, `SIMPRO_` env prefix, `extra="ignore"`
- `auth.py`: `AuthManager` — OAuth2 Client Credentials with token caching/refresh, API Key fallback
- `client.py`: `SimproClient` base HTTP client — GET/POST/PATCH/DELETE, 401 retry-once, structured error handling
- `exceptions.py`: typed exception hierarchy (`SimproError`, `SimproAuthError`, `SimproAPIError`, `SimproRateLimitError`, `SimproNotFoundError`)
- `logging.py`: `ContextVar`-based correlation IDs, JSON log formatter, `RequestTimer`
- 18 unit tests added (`test_auth.py`, `test_client.py`, `test_config.py`, `test_logging.py`), respx-mocked, all offline

### Architecture Pivot (planning)
- Confirmed: no live Simpro Premium API access available to CVC
- Decision recorded (`docs/ADR/adr-mock-simpro-api.md`): build a high-fidelity mock service before the typed client layer, so only `SIMPRO_BASE_URL`/`SIMPRO_TOKEN_URL` need to change when live access arrives
- Confirmed OAuth strategy: Client Credentials Grant for the backend integration; Authorization Code Grant deferred to a future user-facing portal (Phase 6+)
- Confirmed multi-company model: `CVC Service` (`company_id=1`), `CVC Projects` (`company_id=2`)

### Sprint 3 — Simpro Mock Service
- Created `services/simpro_mock/` FastAPI service, own dedicated Postgres container (`simpro-mock-db`, port 5433), kept separate from the Phase 2 PGVector database
- Modelled and seeded 12 resources: Companies, Customers, Jobs, Quotes, Contacts, Sites, Assets, Employees, Projects, Job Notes, Attachments, Statuses
- Implemented `BearerAuthMiddleware`, Simpro-style operator filtering (`gt()`, `lt()`, `le()`, `ge()`, `ne()`, `between()`, `in()`, `!in()`, `search=all|any`), and pagination headers (`Result-Total`, `Result-Count`, `Result-Pages`)
- Alembic migrations (`876a0e057b67_init_db.py`, `27082026_add_simpro_resources.py`)
- Added to `docker-compose.yml` on port 8100
- ADR written: `docs/ADR/adr-mock-simpro-api.md`

### Sprint 3 Review / Hardening Fixes
- Rewrote the live-mock integration test as a properly skip-gated pytest module (`tests/test_simpro_mock_v2.py`), guarding on mock reachability rather than failing collection outright
- Moved the manual diagnostic script with `test_*`-named helper functions out of `tests/` to `scripts/verify-simpro-mock.py`, eliminating phantom pytest collection
- Fixed an unreachable branch in `client.py`'s correlation-ID handling; correlation IDs are now propagated on the outgoing `X-Correlation-ID` request header
- Normalized `simpro_mock/models.py` to consistent SQLAlchemy 2.0 `Mapped[]`/`mapped_column` style with `back_populates` on every relationship
- Normalized `simpro_mock/schemas.py` to consistent `str | None` typing (previously mixed with `Optional[str]`)
- Cleaned git history: untracked an accidentally committed `.venv/`, amended the Sprint 1 commit, force-pushed with `--force-with-lease`

### Documentation Catch-Up (this delivery)
- Generated: Phase 3 as-built PDD, platform architecture doc, expanded `docs/phase3.md`, Simpro mock API reference, development standards, testing guide, installation guide, roadmap, known-issues log
- Flagged for follow-up: legacy `tests/test_simpro_mock.py` still present alongside its replacement; `structure.txt` stale; `RevisedScope.txt`'s "Sprint 4" narrative ahead of what's in the code

## Not Yet Started
- `simpro_client/models/` and `simpro_client/endpoints/` (typed Pydantic models + endpoint modules)
- Client-side pagination iterator and token-bucket rate limiter
- Phase 3 → Phase 4 handoff ADR (direct import vs. service wrapper)
- Phase 4 (Document Generation) — blocked on the above
