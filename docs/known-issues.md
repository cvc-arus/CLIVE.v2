# Known Issues & Discrepancies

Found by reading the actual codebase and running the test suite, per the project's "code is the source of truth" principle. Entries are fixed only when a sprint does so; a resolved entry is kept and marked, rather than deleted, so the original finding stays on the record. The rest should be triaged before Phase 3 sign-off.


## `pip install -e ".[dev]"` warns and silently skips dev dependencies

The root `pyproject.toml` defines dev dependencies under `[dependency-groups]` (PEP 735 style) rather than `[project.optional-dependencies]`. `pip install -e ".[dev]"` prints `WARNING: simpro-client 0.1.0 does not provide the extra 'dev'` and installs only the base package — `pytest`, `respx`, `ruff`, and `pytest-cov` are not installed by that command. `uv sync` (or explicit `pip install pytest respx ruff pytest-cov`) is required instead.

## Unused mock settings `SIMPRO_MOCK_MOCK_CLIENT_ID` and `SIMPRO_MOCK_MOCK_CLIENT_SECRET`

Observed 2026-10-02. `services/simpro_mock/simpro_mock/config.py` defines `mock_client_id` and `mock_client_secret`, but nothing reads them: `issue_token` in `services/simpro_mock/simpro_mock/routers.py` ignores the submitted credentials and always returns the static token. Removing the two settings is a later code task.

## RESOLVED 2026-10-08 — "only `SIMPRO_BASE_URL` changes at cutover" was unverified

Raised 2026-10-07. Five documents asserted that switching from the mock to live
Simpro needed only a configuration change. Nothing tested the claim, and when it
was measured against Simpro's published OpenAPI spec it was false:

- **4 of 12 routes did not exist upstream.** There is no Projects resource, no
  `/customers/{id}`, status codes live at `/setup/statusCodes/projects/`, and
  attachments at `/jobs/{id}/attachments/files/`.
- **11 of 12 client models rejected payloads generated from the vendor's own
  contract.** Only `Company` passed. `Job.Status` and `Job.Total` were modelled
  as a string and a float where the spec has nested objects; money was `float`
  where the spec constrains it to two decimal places; several fields were marked
  required that the real API omits.
- **Nothing tested that `simpro_client` could reach `simpro_mock` at all**, so
  either side could have been changed alone and the suite would have stayed
  green.

Resolved by ADR-013 across seven sprints. The claim is now enforced rather than
asserted: `tests/test_spec_conformance.py` generates payloads from the vendored
contract (`docs/contracts/simpro-openapi-v1-get-subset.json`) and validates every
client model against them, on both the list and detail legs, in both a full and a
minimal shape. **Every check passes and `tests/spec_conformance_baseline.json`
is empty**, where 40 of 44 combinations failed when the baseline was first
recorded. Run `uv run pytest -q tests/test_spec_conformance.py` for the current
result.
`tests/test_client_mock_drift.py` additionally drives the real client against the
running mock, so a one-sided change now fails.

Two caveats remain, both deliberate and documented in
`services/simpro_mock/CLAUDE.md` §3:

- The contract is the vendor's **published** spec, not observed live traffic.
  Where the spec is itself wrong, the code is wrong with it.
- Three behaviours cannot be verified without live access: whether Simpro
  always returns `ID` in a `columns` projection, whether the `Result-*`
  pagination headers exist (they are real but absent from the spec), and the
  exact default projection of routes the mock narrows by hand.

## Existing lint debt

Observed 2026-10-02. `uv run ruff check .` and `uv run ruff format --check .` do not pass on the existing code in `src/`, `tests/`, `services/`, `scripts/` and on Python blocks in some Markdown files. Run the commands for the current count. New and modified code must be lint-clean (root `CLAUDE.md` §7); clearing the existing errors is a later code task.
