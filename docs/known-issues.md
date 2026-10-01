# Known Issues & Discrepancies (Observed 2026-09-04)

Found by reading the actual codebase and running the test suite, per the project's "code is the source of truth" principle. None of these are fixed here — this is a documentation pass, not a code change — but they should be triaged before Phase 3 sign-off.



**Recommendation:** regenerate `structure.txt` (e.g. `tree -L 5 -I 'venv|__pycache__|.git' >structure.txt`) as part of closing out Phase 3.


## `pip install -e ".[dev]"` warns and silently skips dev dependencies

The root `pyproject.toml` defines dev dependencies under `[dependency-groups]` (PEP 735 style) rather than `[project.optional-dependencies]`. `pip install -e ".[dev]"` (as documented in the existing `docs/phase3.md`) prints `WARNING: simpro-client 0.1.0 does not provide the extra 'dev'` and installs only the base package — `pytest`, `respx`, `ruff`, and `pytest-cov` are not installed by that command. `uv sync` (or explicit `pip install pytest respx ruff pytest-cov`) is required instead.

##  `RevisedScope.txt` describes Sprint 4 as further along than the code shows

`RevisedScope.txt` marks "Sprint 4 — Typed Client Layer" as "🔶 In Progress


