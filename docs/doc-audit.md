# Doc check: all documents

**The check found 47 problems:**

| Severity | Count |
|---|---|
| Wrong | 20 |
| Stale | 13 |
| Unverifiable | 3 |
| Structure | 11 |

`roadmap.md` and `architecture.md` are the worst: both say the typed models, endpoints and rate limiter don't exist yet, but all three are in the code and tested.

**Commit and scope:** HEAD is `f2795e2`, plus the staged, uncommitted changes. The scope `all` covers every document listed in `docs/README.md`:

- **Living:** `README.md`, `roadmap.md`, `architecture.md`, `installation.md`, `development-standards.md`, `testing.md`, `known-issues.md`, `CHANGELOG.md`
- **Reference:** `simpro-mock-api-reference.md`, `services/simpro_mock/configuration.md`, `structure.txt`
- **Decision:** `ADR-index.md`, the eleven ADRs, the four PDDs (links and index only)
- **Historical:** 11 files (links and headers only)
- **The index itself:** `docs/README.md`

**What I ran:**
- `pytest --collect-only -q`: 58 tests collected.
- Earlier this session, at the same HEAD with no code changed since: `pytest -q -m "not integration"` gave 56 passed, 2 deselected.
- `uv pip install --dry-run -e ".[dev]"` warned "does not have an extra named `dev`".
- Code checks against `routers.py`, `schemas.py`, `config.py`, `seed.py`, `filtering.py`, `docker-compose.yml` and `.env.example`.
- `git status --short`: no tracked `__pycache__` files are modified, so there is nothing to restore.

## Findings

| Document | Line / section | Claim | Actual (evidence) | Severity | Suggested fix |
|---|---|---|---|---|---|
| `README.md` | 44–53, 273 | Phase 3 is "Planned" | Phase 3 code exists in `src/simpro_client/` and `services/simpro_mock/`; `roadmap.md` says "In progress" | wrong | Replace both status blocks with a link to `docs/roadmap.md` (its owner) |
| `README.md` | 112–262 | Repository tree | Copies `structure.txt`, which is itself out of date; shows `pagiantion and retries.md` and "25 directories, 122 files" | structure | Replace with a link to `structure.txt` |
| `README.md` | 317–329 | Sprint template list | Lacks Implementation, Documentation updates and Git commit, which `development-standards.md` §8 lists | structure | Link to `development-standards.md` §8 |
| `roadmap.md` | 3, 27, 32, 41 | Built from `RevisedScope.txt` and `# CLIVE Enterprise AI Platform.txt` | Neither file is in the repo (`git ls-files` finds nothing) | unverifiable | Say where these files live, or drop the references |
| `roadmap.md` | 9 | "typed models/endpoints layer not started in code" | `src/simpro_client/models/` and `endpoints/` exist; collect-only finds 13 tests in `test_models.py` and 14 in `test_endpoints.py` | wrong | Update the Phase 3 notes |
| `roadmap.md` | 21–23 | Remaining work: build `models/` and `endpoints/`, add `pagination.py` and `rate_limiter.py` | All built. Pagination lives in `endpoints/base.py` (`fetch_page`/`iter_all`); `rate_limiter.py` exists | stale | Mark items 2–4 done; pagination is in `endpoints/base.py` |
| `roadmap.md` | 23 | Rate limiter is "per the original ADR-005 recommendation" | ADR-005 is the auth strategy; rate limiting is in ADR-010 (ADR-008 was withdrawn) | wrong | Change to ADR-010 |
| `roadmap.md` | 20, 24 | "Record the handoff ADR"; "remove legacy `tests/test_simpro_mock.py`" | ADR-009 exists as Proposed; the test file was deleted in `9b7cf3d` | stale | Item 1 becomes "decide ADR-009"; remove the deleted-file task |
| `architecture.md` | 15 | Phase 3: "typed client layer not started" | Same evidence as the `roadmap.md` line 9 finding; also repeats phase status, which `roadmap.md` owns | wrong / structure | Link to `roadmap.md` |
| `architecture.md` | 62 | Requests funnel through `_request()` to `_handle_response()` | There is no `_handle_response`; the funnel is `_request_response()` (`client.py:95`) | wrong | Rename the methods |
| `architecture.md` | 63 | Exception hierarchy: `SimproAPIError` → `SimproRateLimitError`, `SimproNotFoundError` | `exceptions.py:35–74` adds `SimproClientError`, `SimproServerError` and `SimproProtocolError`; 404 and 429 errors subclass `SimproClientError` | stale | Update the hierarchy |
| `architecture.md` | 66–72 | 429 raises an error; any other ≥400 raises `SimproAPIError` | 429 is retried up to `max_retries`, then raises; other 4xx raise `SimproClientError`; 5xx raise `SimproServerError`; network errors raise `SimproAPIError` with status 0 (`client.py:115–153`) | stale | Update the list |
| `architecture.md` | 74 | "Not yet present: `models/`, `endpoints/`, `pagination.py`, `rate_limiter.py`" | The first, second and fourth exist; pagination is in `endpoints/base.py` | wrong | Rewrite this line only |
| `architecture.md` | 93 | `routers.py` has "25 routes" | 26: health, token and 24 GET routes (`grep -cE '@(api\|health\|token)_router\.'` = 26) | wrong | Change to 26 |
| `architecture.md` | 145 (§6) | Handoff "has not been recorded as an ADR yet" | `docs/ADR/adr-009-phase3-phase4-handoff.md` exists with status Proposed | stale | Say "recorded as ADR-009 (Proposed, open)" |
| `installation.md` | 23, 38 | `.env.example` has a Postgres/PGVector section | `.env.example` has only `SIMPRO_*` keys; `POSTGRES_DB`/`USER`/`PASSWORD` are missing | wrong | Say the Postgres keys must be added by hand (or add them to `.env.example`) |
| `installation.md` | 25–36 | Env sample | Omits `SIMPRO_LIMITER_CAPACITY` and `SIMPRO_LIMITER_REFILL_RATE`, which are in `.env.example:27–28` | stale | Add the two lines, or point to `.env.example` instead of copying it |
| `installation.md` | 92 | `uv pip install -e ".[dev]"` understands dependency groups | Dry run warns "does not have an extra named `dev`" | wrong | Recommend only `uv sync` |
| `installation.md` | 97–100 | "18 tests pass offline" | 58 collected; 56 pass offline; a test count in a living doc goes stale | wrong / structure | Give the command `uv run pytest -q -m "not integration"` without a count |
| `installation.md` | 119 | `docker compose down -v` "destroys all data" | Only named volumes are removed. Phase 1/2 data is in `/data/` bind mounts (compose lines 9, 25, 52); the unused named volumes (lines 103–105) are also removed | wrong | Say what `-v` actually removes, and that it needs Alex's approval |
| `installation.md` | 126 | Volume name `clive-i_simpro-mock-db-data` | Can't confirm without Docker (the doc itself says the name may vary) | unverifiable | None |
| `installation.md` | 137 | Legacy `tests/test_simpro_mock.py` | Deleted in `9b7cf3d` | stale | Delete the row |
| `development-standards.md` | 3, 75 | Sources: `Clive_Scope.txt`, `__CLIVE_Enterprise_AI_Platform.txt` | Not in the repo | unverifiable | Same as for `roadmap.md` |
| `development-standards.md` | 10 | Formatting with "`ruff format` / `black`" | `black` is not a dependency (root `pyproject.toml` dev group) | wrong | Remove `black` |
| `development-standards.md` | 12 | Docstrings on all public classes and functions | `client.py` has almost none (`client.py:45–198`) | wrong | Say "required on new or modified code" |
| `development-standards.md` | 21–22 | `ruff check src/ --fix`; `ruff format src/` | Root `CLAUDE.md` §7 forbids running `--fix`/`format` outside your change; the commands also lack `uv run` | wrong | Use `uv run ruff check <paths>` and `uv run ruff format --check <paths>` |
| `development-standards.md` | 28 | "All 18 tests in 4 files" | 58 tests in 11 modules | stale / structure | Drop the count; link to `testing.md` |
| `development-standards.md` | 29 | The integration test uses `pytest.mark.skipif` | Runtime `pytest.skip()` in an autouse fixture (`test_simpro_mock_v2.py:10–20`) | wrong | Say "skips at runtime" |
| `development-standards.md` | 31 | `tests/test_simpro_mock.py` is still present | Deleted | stale | Remove the bullet |
| `development-standards.md` | 56 | `.env.example` documents every required key | `POSTGRES_*` keys are missing | wrong | Narrow to "every `SIMPRO_` key", or add the Postgres keys |
| `testing.md` | 7–14 | 4 files, 18 tests | 11 test modules, 58 collected | stale | For the planned `testing.md` update session |
| `testing.md` | 34 | Uses `pytest.mark.skipif` | Skips at runtime (as for `development-standards.md` line 29) | wrong | Same |
| `testing.md` | 35 | `tests/test_simpro_mock.py` exists | Deleted | stale | Same |
| `testing.md` | 54–58 | `ruff --fix`/`format src/`; "zero-error linting expected" | Contradicts root `CLAUDE.md` §7; `ruff check .` reports 83 errors (run earlier this session) | wrong | Same |
| `known-issues.md` | 5–7 | A bare "Recommendation" with a `tree -L 5` command | No heading, and the command differs from `docs/README.md` §4 | structure | Remove it; `docs/README.md` §4 owns the command |
| `known-issues.md` | 12 | "As documented in the existing `docs/phase3.md`" | `docs/phase3.md` doesn't exist | stale | Remove the clause |
| `known-issues.md` | 14–16 | `RevisedScope.txt` issue | Cut off mid-sentence, and the source file isn't in the repo | structure / unverifiable | Finish the entry or remove it |
| `CHANGELOG.md` | 51–55 | "Documentation Catch-Up" | Garbled fragments ("… rate limiter- STARTED"); refers to the missing `docs/phase3.md` | structure | Rewrite just this block |
| `CHANGELOG.md` | — | Sprint 4 entries | Sprint 4 code (`d83b568`, `d6723d8`: models, endpoints, pagination, retries, limiter) has no entry | stale | Add a Sprint 4 entry |
| `CHANGELOG.md` | 60 | Handoff ADR "not yet started" | ADR-009 exists as Proposed | stale | Say "drafted, undecided" |
| `simpro-mock-api-reference.md` | 173–174 | Attachments are seeded "proportionally" per company | Only the first 10 jobs get attachments (`seed.py:369`): 8 belong to company 1 and 2 to company 2 | wrong | Say "attachments on the first 10 jobs" |
| `configuration.md` | 19, 24 | The token route expects `SIMPRO_MOCK_MOCK_CLIENT_ID` and `_SECRET` | Never read: they appear only in `config.py:6–7`; `issue_token` ignores them (`routers.py:61–76`) | wrong | Mark both as unused |
| `configuration.md` | 40 | A `.env` file in `services/simpro_mock/` overrides settings | `Settings` has no `env_file` (`config.py:11` sets only `env_prefix`), so the file is never read | wrong | Use real environment variables or Compose `environment:` |
| `structure.txt` | whole file | Generated tree | No header; old pagination filename; includes untracked `dock/phase1`; omits tracked `.claude/`, `.env.example`, `.gitignore`, `tests/__pycache__` | stale | Regenerate with the `docs/README.md` §4 command |
| `docs/README.md` | §3, `known-issues` row | "Stale: #6 contradicted by code" | `known-issues.md` has no numbered items now | stale | Reword the row |
| `ADR-index.md` | 3, 20–23 | — | Leftover chat text ("Place these files…", "Two items need your attention…") and a dangling "**ADR-010**" | structure | Delete lines 3 and 20–23 |
| PDDs | `PDD-phase1:4`, `PDD-phase2:4`, `PDD-phase3:97,117–118`, `PDD-phase4:12` | Links | `docs/phase1.md`, `docs/phase2.md`, `tests/test_simpro_mock.py`, `test_simpro_integration.py` and `adr-006-phase3-phase4-handoff.md` don't exist | structure | Fix the paths (e.g. `docs/phase1/summary.md`, `adr-009-…`) |
| Historical (11 files) | line 1 | `> Historical record as of …` header | Missing from all 11 (grep finds 0 in each) | structure | Already a to-do in `docs/README.md` §6 |
| `phase3/phase3-summary.md` | 3, 58, 63, 164 | Links | `docs/phase3.md`, `docs/phase3-logging.md` and `docs/PDD-phase3.md` don't exist (actual: `docs/phase3/logging.md`, `docs/PDDs/PDD-phase3.md`); `scope/scope&readmap-rev2.md:66` also links `docs/phase3.md` | structure | Add a dated correction note when asked |

## Summary

**Clean documents:**
- **Indexing:** every file under `docs/` is listed in `docs/README.md`.
- **ADRs:** every ADR in `docs/ADR/` is in `ADR-index.md` with a status that matches the file.
- **ADR status sections:** each file's own status matches the index.
- **`simpro-mock-api-reference.md`:** clean apart from the seed-volume line. Routes, field nullability, auth error messages, the health response, pagination limits and filtering all match the code.

**Partly unchecked:**
- **Relationship claims:** the `back_populates` / `CASCADE` claims in `architecture.md` and `development-standards.md` were only spot-checked (36 `back_populates` in `models.py`).
- **Docker claims:** container behaviour couldn't be confirmed without Docker.

## Needs your decision

1. **Where `RevisedScope.txt`, `Clive_Scope.txt` and `# CLIVE Enterprise AI Platform.txt` live.** Four living documents cite them as sources, but they aren't in the repo. Should I add them, link to them, or drop the citations?
2. **Postgres keys in `.env.example`.** Should `.env.example` include `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD`? Otherwise `installation.md` and `development-standards.md` should stop saying it does.
3. **`README.md` content.** Should it keep its own status, tree and template sections? Under the "one fact, one home" rule they should become links to `roadmap.md`, `structure.txt` and `development-standards.md`.
4. **Ruff rules.** `development-standards.md` and `testing.md` tell people to run `ruff --fix` / `ruff format` and expect zero lint errors. Root `CLAUDE.md` §7 forbids both, and the lint debt is real (83 errors). Which rule wins?
5. **Unused mock settings.** `SIMPRO_MOCK_MOCK_CLIENT_ID` and `_SECRET` are never read. Should I document them as unused, or open a task to remove them? Removing them is a code change.
