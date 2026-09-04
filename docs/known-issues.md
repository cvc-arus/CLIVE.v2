# Known Issues & Discrepancies (Observed 2026-09-04)

Found by reading the actual codebase and running the test suite, per the project's "code is the source of truth" principle. None of these are fixed here — this is a documentation pass, not a code change — but they should be triaged before Phase 3 sign-off.

## 1. Duplicate mock-integration test file

`tests/test_simpro_mock.py` (legacy, module-level `assert`s, requires a live mock unconditionally) is still present in the repository alongside `tests/test_simpro_mock_v2.py` (the corrected, skip-gated replacement). Running `pytest tests/` will fail on `test_simpro_mock.py` specifically if `simpro-mock` isn't running, because that file does not skip gracefully.

**DELETED**Recommendation:** delete `tests/test_simpro_mock.py`; keep only `test_simpro_mock_v2.py`.

**FIXED**## 2. `structure.txt` is stale

The committed `structure.txt` (a project-tree snapshot) does not reflect the current tree:
- Lists `tests/test_simpro_integration.py`, which no longer exists (it was moved to `scripts/verify_simpro_mock.py` per the Sprint 3 fixes).
- Does not list `services/simpro_mock/` at all.
- Does not list `tests/test_simpro_mock_v2.py`.
- Does not list `scripts/verify-simpro-mock.py`.

**Recommendation:** regenerate `structure.txt` (e.g. `tree -L 5 -I 'venv|__pycache__|.git' >structure.txt`) as part of closing out Phase 3.

**REPLACED WITH NEW phase3.md**## 3. `docs/phase3.md` (pre-existing) only documents Sprint 1

The existing `docs/phase3.md` describes the `simpro_client` foundation only and makes no mention of `services/simpro_mock/` at all, despite the mock being fully built, seeded, and Dockerized. This document set replaces it with an expanded version (see `docs/phase3.md` in this delivery) covering both halves of Phase 3.

## 4. `docker-compose.yml` declares unused named volumes

The bottom of `docker-compose.yml` declares `ollama_data`, `openwebui_data`, and `pgvector_data` as named volumes, but the `ollama`, `open-webui`, and `postgres` services actually use host bind-mounts (`/data/ollama`, `/data/openwebui_data`, `/data/pgvector_data`) instead. Only `simpro-mock-db-data` is an actively used named volume. This is cosmetic (the unused declarations are harmless) but should be cleaned up for clarity.

## 5. `pip install -e ".[dev]"` warns and silently skips dev dependencies

The root `pyproject.toml` defines dev dependencies under `[dependency-groups]` (PEP 735 style) rather than `[project.optional-dependencies]`. `pip install -e ".[dev]"` (as documented in the existing `docs/phase3.md`) prints `WARNING: simpro-client 0.1.0 does not provide the extra 'dev'` and installs only the base package — `pytest`, `respx`, `ruff`, and `pytest-cov` are not installed by that command. `uv sync` (or explicit `pip install pytest respx ruff pytest-cov`) is required instead.

## 6. `RevisedScope.txt` describes Sprint 4 as further along than the code shows

`RevisedScope.txt` marks "Sprint 4 — Typed Client Layer" as "🔶 In Progress," describing work on `models/`, `endpoints/`, `pagination.py`, and `rate_limiter.py`. None of these exist in `src/simpro_client/` at the time of this review — only the Sprint 1 foundation (`config.py`, `auth.py`, `client.py`, `exceptions.py`, `logging.py`) is present. Whether this means the typed-layer work simply hasn't been committed yet, or the planning document is ahead of reality, should be clarified before continuing to reference "Sprint 4" as in-progress in future planning.

## 7. `simpro_mock/schemas.py` style inconsistency — resolved

A previously flagged inconsistency (mixing `Optional[str]` and `str | None` across schema fields) is **no longer present**. All fields in `schemas.py` now consistently use `str | None`. No action needed; noted here only to close out the item.
