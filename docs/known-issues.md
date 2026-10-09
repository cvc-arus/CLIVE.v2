# Known Issues & Discrepancies

Found by reading the actual codebase and running the test suite, per the project's "code is the source of truth" principle. Entries are fixed only when a sprint does so; a resolved entry is kept and marked, rather than deleted, so the original finding stays on the record. The rest should be triaged before Phase 3 sign-off.


## `pip install -e ".[dev]"` warns and silently skips dev dependencies

The root `pyproject.toml` defines dev dependencies under `[dependency-groups]` (PEP 735 style) rather than `[project.optional-dependencies]`. `pip install -e ".[dev]"` prints `WARNING: simpro-client 0.1.0 does not provide the extra 'dev'` and installs only the base package — `pytest`, `respx`, `ruff`, and `pytest-cov` are not installed by that command. `uv sync` (or explicit `pip install pytest respx ruff pytest-cov`) is required instead.

## RESOLVED 2026-10-08 — unused mock settings `SIMPRO_MOCK_MOCK_CLIENT_ID` and `SIMPRO_MOCK_MOCK_CLIENT_SECRET`

Observed 2026-10-02. `services/simpro_mock/simpro_mock/config.py` defined `mock_client_id` and `mock_client_secret`, but nothing read them: `issue_token` in `services/simpro_mock/simpro_mock/routers.py` ignores the submitted credentials and always returns the static token.

**Resolved 2026-10-08.** Both fields are removed from `Settings`, and
`services/simpro_mock/configuration.md` no longer documents the two variables
(its entries are renumbered 1–3). Two checks made removal safe: the
`simpro-mock` service in `docker-compose.yml` passes only
`SIMPRO_MOCK_DATABASE_URL`, so the variables were never supplied to the
container; and `Settings` tolerates unrecognised prefixed environment
variables, verified by instantiating the trimmed model with both set, so a
leftover value in anyone's environment cannot stop the service booting.

The route still accepts any `client_id` and `client_secret`. That is a
documented limitation of `adr-mock-simpro-api.md`, not an unimplemented
feature, so validating them would need that ADR changed first; the settings
were removed rather than wired up for exactly that reason. `issue_token` keeps
both as **form fields**, which are request inputs and were never related to
the settings.

## RESOLVED 2026-10-08 — the mock accepted `orderby` and `limit` and silently ignored them

Observed 2026-10-08. `services/simpro_mock/simpro_mock/filtering.py` lists both
in `PAGINATION_PARAMS`, so they are skipped as request controls rather than
rejected as unknown filters, and nothing implements either: there is no
`order_by` anywhere in `routers.py`, and the only `.limit()` in the service is
`paginate_query`'s `page_size`. A caller who sends `?orderby=Name` or
`?limit=10` therefore receives a `200` with unsorted, unlimited data and no
indication that the parameter did nothing.

This was the same failure class that ADR-013 S6 fixed for filter parameters,
which raise `UnknownFilterParameterError` and return a `400`. S6's scope was
`columns` only, so these two were left behind.

**Resolved 2026-10-08.** Both are now honoured on all 13 collection routes.
`orderby` is implemented in the new
`services/simpro_mock/simpro_mock/ordering.py`: a csv list of wire column
names, with a `-` prefix for descending, translated through the same
`FILTER_MAPS` that filters use, because the orderable set is the scalar
columns. An unorderable field returns a `400` naming the fields that would
have worked, matching what S6 did for filters — implementing them rather than
rejecting them, because real Simpro honours both and a `400` would have been a
divergence from upstream. `limit` narrows the effective page size in
`paginate_query`.

One caveat carried forward: the contract describes `limit` only as "Set the
limit of number of records in a request", so **its exact upstream semantics are
unverified**. The mock reads it as a narrowing of `pageSize`; "in a request"
could instead mean a cap on the whole result set across pages. Re-check on
first live access.

## RESOLVED 2026-10-08 — collection routes paginated without an `ORDER BY`

Observed 2026-10-08 while verifying the entry above.
`paginate_query` in `services/simpro_mock/simpro_mock/middleware.py` applies
`.offset().limit()` to a query that has no ordering, and no route in
`routers.py` adds one (`grep -c order_by` returns 0). PostgreSQL gives no
ordering guarantee for an unordered query, so page boundaries are not
guaranteed stable: in principle a row can repeat on two pages or be skipped
entirely while `iter_all()` walks them.

In practice the seeded tables were small and returned in insertion order, which
is why no test caught it, but the behaviour was not enforced anywhere.

**Resolved 2026-10-08.** Every paginated query now goes through
`ordering.apply_ordering`, which orders by `id` when no `orderby` was given and
always appends `id` as the final tiebreak otherwise — `orderby=Name` over rows
sharing a name would be just as unstable as no ordering at all.
`tests/test_simpro_mock_v2.py::test_collection_pagination_visits_every_row_exactly_once`
walks a collection two rows at a time and asserts the walk covers
`Result-Total` rows with no repeat.

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
