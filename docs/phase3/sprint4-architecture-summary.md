# Phase 3 Architecture Summary

This summary preserves the repository baseline, environmental parameters, and emergency recovery vectors for Sprint 4.

## 1. Repository Baseline
*   **Baseline Commit (Sprint 1 Root):** `5c393e2ab8a5b92f64bdfaf497e13af4902847e9`
*   **Environment Verification:** Checked via local `uv` toolchain running version `0.12.9`.
*   **Test Suite Health:** The initial baseline is frozen with 20 discovered tests collected successfully:
    ```bash
    uv run pytest --collect-only -q
    ```

---

## 2. Sprint 4 File Boundary Protection
To protect previous deliverables from accidental modification or file corruption, a strict directory-level boundary is enforced:

*   **Allowed Modifications / Additions:**
    *   `src/simpro_client/models/` (Pydantic model modules)
    *   `src/simpro_client/endpoints/` (Endpoint modules)
    *   `src/simpro_client/pagination.py` (Lazy iteration logic)
    *   `src/simpro_client/rate_limiter.py` (Token bucket limiter)
    *   `src/simpro_client/exceptions.py` (Extended exceptions hierarchy)
    *   `src/simpro_client/config.py` (Limiter configuration variables)
    *   `tests/` (Test additions like `test_models.py`, `test_endpoints.py`, `test_pagination.py`)
    *   `pyproject.toml` (Registration of the `integration` marker)
    *   `.env.example` (Rate limiting capacity parameters)
*   **Strictly Prohibited Mod/Write Targets:**
    *   Any migration scripts under `services/simpro_mock/alembic/`
    *   Core mock server databases/models under `services/simpro_mock/simpro_mock/`
    *   *Note: Async operations and write endpoints remain outside of Sprint 4 scope.*

---

## 3. Environment & Configuration Variables
The client uses standard configuration loading handled by Pydantic-Settings, referencing the local `.env` environment file:

```env
# Existing Sprint 1 config keys
SIMPRO_BASE_URL="http://localhost:8000"
SIMPRO_CLIENT_ID="mock-client-id"
SIMPRO_CLIENT_SECRET="mock-client-secret"

# Additive Sprint 4 Configuration
SIMPRO_LIMITER_CAPACITY=8
SIMPRO_LIMITER_REFILL_RATE=8.0
SIMPRO_MAX_RETRIES=3
```

---

## 4. Disaster Recovery & Rollback Vector
Should the workspace state encounter corrupt edits, dependency mismatches, or testing locks, run this recovery sequence:

```bash
# 1. Force down any active Docker containers and clear volatile networks
docker compose down

# 2. Reset the git workspace, cleanly removing untracked or dirty local files
git reset --hard HEAD
git clean -fd

# 3. Synchronize virtual environment packages with uv.lock
uv sync

# 4. Verify test baseline is once again green and collected
uv run pytest --collect-only -q
```
