# W1 — Simpro Access and Live API Checks

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | — |
| **Related** | `docs/simpro/simpro-api-findings.md`, ADR-010, ADR-013, ADR-014 |

## Goal

Get CLIVE onto the real Simpro API as early as possible, so `simpro_client` is
checked against real responses. The mock stays for fast offline tests, with its
scope frozen.

**Amended 2026-10-16 (Alex):** Simpro's sandbox is not used. Live API access to
CVC's own build arrived (OAuth2 Client Credentials, credentials in `.env`), and
the checks run against it **read-only**: `GET` requests and the token request
only, nothing written to Simpro, and no client data reaching Claude Code (root
`CLAUDE.md` §3 and §9). The tasks below are rewritten from "sandbox" to "live,
read-only".

## Tasks

### T1 — [HUMAN] Raise Simpro Support cases — **not needed** (Alex, 2026-10-16)
Access arrived without them; Alex's answers are in
`docs/simpro/simpro-api-findings.md` §3. The questions still open there
(rate limits, token lifetime, application-level read-only scoping) are answered
by the live checks in T5 or raised later if needed.

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

### T3 — Prepare live read-only contract tests (do not run them in this task)
Only the `integration` marker is registered today (root `pyproject.toml`).
1. Add a pytest marker `live`, registered in config, skipped unless an explicit
   opt-in variable is set, so that live credentials in `.env` alone never make
   the default run contact Simpro. The tests read the live settings at runtime;
   record that exception to `tests/CLAUDE.md`'s "never depend on `.env`" rule
   in that file.
2. Write read-only contract tests: authenticate; list and fetch each resource
   used by Phase 3B in both configured companies (Service, Projects); validate
   responses with the existing Pydantic models; check pagination headers.
   First checks, from `docs/simpro/mock-vs-public-api.md` §5: token request
   encoding (item 13), token invalidation across instances (item 15),
   `/companies/` headers (item 4), `ID` in projections (item 1).
   *(2026-10-17: the smoke check settled items 1, 4 and 13 — §6; the tests
   pin those results so a regression is caught.)*
3. **GET only**, and **no client data in output**: assertions and messages
   report status codes, counts, field and header names, pass/fail; no response
   values (run with `--tb=no`).
4. Document how to run them in `docs/simpro/simpro-api-findings.md`.
5. Confirm the normal test suite still passes and live tests are skipped.
**Stop point:** test run output showing live tests skipped.

### T4 — Fix high-severity differences (only after Alex reviews T2)
Fix differences rated "breaks client" in the mock and/or client, one resource
at a time, with tests. Skip if T2 finds none.
*(2026-10-17: T2 found none, but the live smoke check found three — items 1,
4 and 17 in `docs/simpro/mock-vs-public-api.md` §6.2 — so T4 applies.)*

### T5 — Run live contract tests (only when Alex asks)
Credentials are already in `.env` (Alex). Alex approved a read-only smoke check
against the live build on 2026-10-16; it was run on 2026-10-17 at `68da1bc` as a
scratch script ahead of T3, with results in `docs/simpro/mock-vs-public-api.md`
§6. T5 proper is the run of the T3 tests. Run the T3 tests with the opt-in set, record
pass/fail and the settled unknowns in `docs/simpro/mock-vs-public-api.md` and
`docs/simpro/simpro-api-findings.md`. Any failures become fix tasks.

## Verification
- `docs/simpro/mock-vs-public-api.md` exists and covers the four unverified behaviours and error responses.
- `uv run pytest -q` passes; `uv run pytest -m live` skips cleanly without the opt-in.

## Rollback
`git revert <commit>`.

## Git commit
`docs(simpro): compare mock against published Simpro API`
`test(simpro): add opt-in live read-only contract tests`

## Acceptance criteria
- [x] Support cases raised and logged — not needed (Alex, 2026-10-16)
- [x] Mock vs public API report complete
- [x] Live read-only smoke check run (2026-10-17, `mock-vs-public-api.md` §6)
- [x] "Breaks client" differences fixed (T4; 2026-10-17, `ID` item under ADR-016, accepted 2026-10-19)
- [x] Live read-only contract tests ready and skipped by default (2026-10-17)
- [ ] `STATUS.md` updated
