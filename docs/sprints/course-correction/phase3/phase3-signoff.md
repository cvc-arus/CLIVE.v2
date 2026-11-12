> Historical record as of 2026-10-13, commit 8b11657. Not maintained.

# Phase 3 — Sign-off Evidence

Records the evidence for Phase 3's close, captured in course correction task
W6 T1. Current status is in `docs/STATUS.md`; this file is not updated.

## Close

- **Closed:** 2026-10-09, by Alex, once ADR-009 (Phase 3 → Phase 4 handoff) was
  decided: a single `clive-gateway` service imports `simpro_client` and serves
  every other consumer over HTTP. The gateway does not exist yet.
- **Recorded:** `docs/roadmap.md` and `docs/CHANGELOG.md` (2026-10-12, PR #45).
- **Contract conformance:** ADR-013, implemented 2026-10-08.
  `tests/test_spec_conformance.py` validates every client model against
  payloads generated from `docs/contracts/simpro-openapi-v1-get-subset.json`,
  and `tests/spec_conformance_baseline.json` is empty.

## Test evidence

Run on 2026-10-13 against commit `8b11657`, with `simpro-mock` and
`simpro-mock-db` running (both healthy):

```text
$ uv run pytest -q -rs
...
SKIPPED [1] tests/test_client_mock_drift.py:156: customers has no detail route upstream (ADR-013)
240 passed, 1 skipped in 30.86s

$ uv run pytest -q -m "not integration"
181 passed, 60 deselected in 18.33s
```

The one skip is by design: `/customers/` has no detail route upstream, so the
drift test has nothing to compare for it.

Coverage was not measured: `pytest-cov` is in the dev dependency group, but no
coverage run is configured in `pyproject.toml`.

## Carried past the close

Neither item below is a defect in the delivered code; both are in
`docs/known-issues.md`.

- `pip install -e ".[dev]"` does not install dev tools (PEP 735
  `[dependency-groups]`); use `uv sync`.
- Lint debt: cleared repo-wide in PR #47 (2026-10-12), after the close. On
  2026-10-13 at `8b11657`, `uv run ruff check .` reported "All checks passed!"
  and `uv run ruff format --check .` reported "143 files already formatted".
  The `docs/known-issues.md` entry ("Existing lint debt") and the lint baseline
  in root `CLAUDE.md` §7 had not been updated to match.

Four mock behaviours cannot be verified without live Simpro credentials:

1. Whether Simpro returns `ID` in a `columns` projection that did not ask for it.
2. Whether the `Result-Total` / `Result-Count` / `Result-Pages` headers exist
   (they are documented but absent from the published spec).
3. The exact semantics of `limit`.
4. `/companies/` being unpaginated upstream, where the mock pages it.
