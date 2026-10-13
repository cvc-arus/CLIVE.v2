# W1 — Simpro Access and Sandbox

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | — |
| **Related** | `docs/simpro/simpro-api-findings.md`, ADR-010, ADR-013, ADR-015 |

## Goal

Get CLIVE onto the real Simpro API as early as possible. The shared sandbox
lets `simpro_client` be checked against real responses now, instead of waiting
for production access. The mock stays for fast offline tests, with its scope frozen.

## Tasks

### T1 — [HUMAN] Raise Simpro Support cases
Raise the five cases in `simpro-api-findings.md` section 3, sandbox first.
Record case numbers in section 4. Also chase the price and access-level answer.

### T2 — Mock vs published API comparison
0. Read ADR-013 (reshape to published Simpro spec) first. Only compare what
   ADR-013 did not already cover; if it covered all 12 resources, record that
   in the report and reduce this task to a spot-check.
1. Read the public API documentation (https://developer.simprogroup.com/apidoc/)
   for the 12 resources the mock implements.
2. For each resource compare: path, query parameters, pagination headers,
   field names and types, nesting, error responses.
3. Write `docs/simpro/mock-vs-public-api.md`: one table per resource with
   matches, differences, and severity (breaks client / cosmetic / unknown).
4. Do **not** change the mock or client in this task.
**Stop point:** report with a count of differences by severity.

### T3 — Prepare sandbox contract tests (do not run against any live system)
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
Set sandbox credentials in `.env`, run `pytest -m sandbox`, record results in
`simpro-api-findings.md`. Any failures become fix tasks.

## Verification
- `docs/simpro/mock-vs-public-api.md` exists and covers all 12 resources.
- `pytest` passes; `pytest -m sandbox` skips cleanly without credentials.

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
