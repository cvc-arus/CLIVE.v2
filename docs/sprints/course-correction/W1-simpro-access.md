# W1 — Simpro Access and Sandbox

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | — |
| **Related** | `docs/simpro/simpro-api-findings.md`, ADR-010, ADR-013, ADR-014 |

## Goal

Get CLIVE onto the real Simpro API as early as possible. The shared sandbox
lets `simpro_client` be checked against real responses now, instead of waiting
for production access. The mock stays for fast offline tests, with its scope frozen.

## Tasks

### T1 — [HUMAN] Raise Simpro Support cases
Raise the five cases in `docs/simpro/simpro-api-findings.md` section 3, sandbox first.
Record case numbers in section 4. Also chase the price and access-level answer.

### T2 — Check what ADR-013 left unverified
ADR-013 (implemented 2026-10-08) already compared the mock and client with
Simpro's published spec, vendored at
`docs/contracts/simpro-openapi-v1-get-subset.json`: all 50 conformance checks
pass (`tests/test_spec_conformance.py`). The mock now serves 25 GET routes over
11 resources; Projects was removed because upstream a project is a Job with
`Type="Project"`. The public portal (https://developer.simprogroup.com/apidoc/)
returned HTTP 403 to this environment when ADR-013 was written. So this task
covers only what the spec cannot settle:
1. The four behaviours `docs/roadmap.md` lists as unverifiable without live
   credentials: whether `ID` is returned in a `columns` projection that did not
   ask for it; whether the `Result-Total` / `Result-Count` / `Result-Pages`
   headers exist; `limit`'s exact semantics; `/companies/` being unpaginated
   upstream.
2. Error responses (status codes and bodies), which the GET subset does not cover.
3. Record what the public documentation says on each point, or "not stated",
   in `docs/simpro/mock-vs-public-api.md` (created by this task) with severity (breaks client /
   cosmetic / unknown).
4. Do **not** change the mock or client in this task.
**Stop point:** report with a count of differences by severity.

### T3 — Prepare sandbox contract tests (do not run against any live system)
Running them later needs Alex's approval of an exception to root `CLAUDE.md` §3
(code and tests must never contact `*.simprosuite.com`). Only the `integration`
marker is registered today (root `pyproject.toml`).
1. Add a pytest marker `sandbox`, registered in config, skipped unless
   `SIMPRO_SANDBOX_BASE_URL` and credentials are set.
2. Write read-only contract tests: authenticate; list and fetch each resource
   used by Phase 3B; validate responses with the existing Pydantic models;
   check pagination headers.
3. Document how to run them in `docs/simpro/simpro-api-findings.md`.
4. Confirm the normal test suite still passes and sandbox tests are skipped.
**Stop point:** test run output showing sandbox tests skipped.

### T4 — Fix high-severity differences (only after Alex reviews T2)
Fix differences rated "breaks client" in the mock and/or client, one resource
at a time, with tests. Skip if T2 finds none.

### T5 — [HUMAN, when sandbox access arrives] Run contract tests
Set sandbox credentials in `.env`, run `uv run pytest -m sandbox`, record results in
`docs/simpro/simpro-api-findings.md`. Any failures become fix tasks.

## Verification
- `docs/simpro/mock-vs-public-api.md` exists and covers the four unverified behaviours and error responses.
- `uv run pytest -q` passes; `uv run pytest -m sandbox` skips cleanly without credentials.

## Rollback
`git revert <commit>`.

## Git commit
`docs(simpro): compare mock against published Simpro API`
`test(simpro): add opt-in sandbox contract tests`

## Acceptance criteria
- [ ] Support cases raised and logged
- [ ] Mock vs public API report complete
- [ ] Sandbox contract tests ready and skipped by default
- [ ] `STATUS.md` updated
