# CLIVE Installation & Setup Guide (Phases 1–3)

Target environment: Ubuntu Desktop 24.04 LTS, Python 3.12.3, Docker + Docker Compose.

## 1. Prerequisites

- Docker & Docker Compose installed
- Python 3.12.3
- `uv` (or `pip`) for Python package management
- NVIDIA drivers + Container Toolkit (for the Ollama GPU reservation, if using GPU inference)
- Git

## 2. Clone the Repository

```bash
git clone git@github.com:cvc-arus/CLIVE-I.git
cd CLIVE-I
git checkout develop
```

## 3. Root Environment File

Create `.env` at the repo root from `.env.example` and fill in real values for the Postgres/PGVector section. The Simpro section can be left at its mock defaults for local development:

```env
# Simpro Connection Config (mock defaults — safe to leave as-is until live access is enabled)
SIMPRO_BASE_URL=http://simpro-mock:8000/api/v1.0
SIMPRO_TOKEN_URL=http://simpro-mock:8000/oauth2/token
SIMPRO_CLIENT_ID=your-client-id-here
SIMPRO_CLIENT_SECRET=your-client-secret-here
SIMPRO_AUTH_MODE=client_credentials
SIMPRO_COMPANY_ID_SERVICE=1
SIMPRO_COMPANY_ID_PROJECTS=2
SIMPRO_TIMEOUT=30.0
SIMPRO_MAX_RETRIES=3
```

Plus the Phase 1/2 Postgres/PGVector variables (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`) that `docker-compose.yml` references directly.

## 4. Start the Full Stack

```bash
docker compose up -d
```

This brings up, in dependency order:
1. `postgres` (PGVector) — waits for healthy before `open-webui` starts
2. `simpro-mock-db` — waits for healthy before `simpro-mock` starts
3. `ollama`, `tika` — no dependencies
4. `open-webui` — depends on `postgres` (healthy), `tika`, `ollama`
5. `simpro-mock` — depends on `simpro-mock-db` (healthy); its container `CMD` runs `alembic upgrade head`, then `python -m simpro_mock.seed`, then `uvicorn` — so the mock is fully migrated and seeded by the time it's reachable

## 5. Verify Phase 1 & 2

```bash
./scripts/verify.sh
```

Checks Ollama and the PGVector database respond correctly. Pull a model if needed:

```bash
docker exec -it clive-ollama ollama pull llama3.2
docker exec -it clive-ollama ollama pull nomic-embed-text
```

Open WebUI: http://localhost:3000

## 6. Verify Phase 3 (Simpro Mock)

```bash
curl http://localhost:8100/health
python scripts/verify-simpro-mock.py
```

`verify-simpro-mock.py` obtains a token, exercises every resource endpoint, and exits non-zero with diagnostics on failure.

## 7. Install `simpro_client` for Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Note:** the root `pyproject.toml` currently defines `[dependency-groups] dev = [...]` (PEP 735 style) rather than `[project.optional-dependencies]`, so `pip install -e ".[dev]"` will warn `does not provide the extra 'dev'` and skip the dev dependencies. Install them explicitly if needed:

```bash
pip install -e .
pip install pytest respx ruff pytest-cov
```

(Or use `uv sync` / `uv pip install -e ".[dev]"`, which understands `[dependency-groups]` natively.)

## 8. Run the Test Suite

```bash
pytest tests/ -v
```

18 tests pass offline (no live services required). To also run the live mock smoke test:

```bash
docker compose up -d simpro-mock
pytest tests/test_simpro_mock_v2.py -v
```

## 9. Backups

```bash
./scripts/backup.sh
```

Dumps, compresses, and verifies the PGVector database (Phase 2). The mock's database (`simpro-mock-db`) is disposable dev/test data and is not part of the backup strategy — it can always be rebuilt from the seed script.

## 10. Rollback

```bash
docker compose down            # stop all services, keep volumes
docker compose down -v         # stop all services AND remove volumes (destroys all data)
```

For `simpro-mock` specifically, since its data is fully reproducible from `seed.py`:

```bash
docker compose stop simpro-mock simpro-mock-db
docker volume rm clive-i_simpro-mock-db-data   # volume name may vary; check `docker volume ls`
docker compose up -d simpro-mock-db simpro-mock
```

## 11. Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `simpro-mock` serves old code after an edit | Dockerfile bakes source at build time | `docker compose build simpro-mock` then `up -d`, not just a restart |
| `uv run ENV_VAR=... command` fails, tries to exec the env var | Argument order | Use `ENV_VAR=... uv run command` |
| `pip install -e ".[dev]"` warns "does not provide the extra 'dev'" | Root `pyproject.toml` uses `[dependency-groups]`, not `[project.optional-dependencies]` | Install dev deps explicitly, or use `uv sync` |
| `pytest` fails to even collect tests | An old script-style test file with module-level asserts requiring a live service | Confirm `tests/test_simpro_mock.py` (legacy) isn't being run standalone; prefer `test_simpro_mock_v2.py` |
| 401 from the mock | Missing/incorrect `Authorization: Bearer <token>` header, or token doesn't match `SIMPRO_MOCK_MOCK_ACCESS_TOKEN` | Re-fetch a token from `/oauth2/token` |
