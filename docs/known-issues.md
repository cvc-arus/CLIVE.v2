# Known Issues & Discrepancies

Found by reading the actual codebase and running the test suite, per the project's "code is the source of truth" principle. None of these are fixed here — this is a documentation pass, not a code change — but they should be triaged before Phase 3 sign-off.


## `pip install -e ".[dev]"` warns and silently skips dev dependencies

The root `pyproject.toml` defines dev dependencies under `[dependency-groups]` (PEP 735 style) rather than `[project.optional-dependencies]`. `pip install -e ".[dev]"` prints `WARNING: simpro-client 0.1.0 does not provide the extra 'dev'` and installs only the base package — `pytest`, `respx`, `ruff`, and `pytest-cov` are not installed by that command. `uv sync` (or explicit `pip install pytest respx ruff pytest-cov`) is required instead.

## Unused mock settings `SIMPRO_MOCK_MOCK_CLIENT_ID` and `SIMPRO_MOCK_MOCK_CLIENT_SECRET`

Observed 2026-10-02. `services/simpro_mock/simpro_mock/config.py` defines `mock_client_id` and `mock_client_secret`, but nothing reads them: `issue_token` in `services/simpro_mock/simpro_mock/routers.py` ignores the submitted credentials and always returns the static token. Removing the two settings is a later code task.

## Existing lint debt

Observed 2026-10-02. `uv run ruff check .` and `uv run ruff format --check .` do not pass on the existing code in `src/`, `tests/`, `services/`, `scripts/` and on Python blocks in some Markdown files. Run the commands for the current count. New and modified code must be lint-clean (root `CLAUDE.md` §7); clearing the existing errors is a later code task.
