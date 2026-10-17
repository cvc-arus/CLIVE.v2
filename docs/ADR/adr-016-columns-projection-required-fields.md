# ADR-016: `columns` projections — the server adds nothing, the client asks for the required fields

- **Status:** Proposed (2026-10-17). Drafted by Claude at Alex's request ("research
  and choose the best option"); implemented on branch
  `fix/w1-live-api-differences` for review. If accepted, supersedes the
  sentence "`ID` is always included." in ADR-013 Decision §5.
- **Date:** 2026-10-17
- **Deciders:** Alex
- **Related:** ADR-013 (re-shape to the published spec; §5 `columns`),
  ADR-009 (`clive-gateway`, the planned caller of projections),
  `docs/simpro/mock-vs-public-api.md` §6 item 1.

## Context

ADR-013 §5 made the mock honour Simpro's `columns` parameter and said "`ID` is
always included". The mock implemented that as `projection.ALWAYS_INCLUDED`,
flagged in its own comments as unverified against live Simpro.

The first read-only live check (2026-10-17) settled it: Simpro returns
**exactly** the columns asked for. `columns=CompanyName` returns only
`CompanyName`; `columns=ID,CompanyName` returns both.

Every client model requires `ID`, and some require more. The vendored contract
marks `ID` required on 76 schemas, and `src/simpro_client/CLAUDE.md` §7 makes a
model field required only when the contract requires it on both the list and
detail legs. The required sets are small: `ID` plus at most five fields (for
example `Job`: `ID`, `Description`, `Total`; the polymorphic customers list:
`ID`, `Type`, `CompanyName`, `GivenName`, `FamilyName`, `_href`).

So a projection that leaves out `ID` passed against the mock and failed
against Simpro. More generally, a projection that leaves out any required
field fails validation, and before this ADR the caller had to know the rule
(`src/simpro_client/CLAUDE.md` §9).

Projections matter for what comes next. Phase 3B's `clive-gateway` (ADR-009)
will build fixed queries that widen Simpro's narrow default list projection
without making one detail call per row, against a limit of 10 requests per
second per build.

## Alternatives Considered

### Option 1 — Mock only: stop inventing `ID`; callers list required fields
The mock matches live behaviour. The client is unchanged, and each caller must
include every required field in `columns`.
- Pro: smallest change; the mock is faithful.
- Con: leaves a trap that is easy to fall into. A missing field fails only at
  runtime, as a `ValidationError` deep inside a gateway query.

### Option 2 — Mock fix, and the client always adds `ID`
- Pro: fixes the case the live check actually hit.
- Con: `ID` becomes a special case. `columns=["Stage"]` on jobs still fails on
  `Description`/`Total`, so callers still need the general rule.

### Option 3 — Make `ID` (or every field) optional in the models
- Con: contradicts the vendored contract that ADR-013 made normative, so
  `test_spec_conformance.py` no longer enforces it.
- Con: every consumer must handle `id is None` on rows that always have one
  in practice.
- Con: does not fix projections that leave out other required fields.

### Option 4 — Mock fix, and the client adds every required field it is missing (recommended)
`ResourceEndpoint._columns_param()` appends the model's required wire names
that the caller left out. The caller's own order is kept and duplicates are
dropped. The list is derived from the model at runtime, so there is no list
to maintain by hand.
- Pro: any projection validates, and models stay exactly as the contract
  defines them.
- Pro: the mock is faithful again, so the mock suites see what Simpro does.
- Pro: one general rule in one place, with no special case for `ID`.
- Con: a projection carries a few more columns than the caller named. That is
  negligible next to the default projection.
- Con: the polymorphic customers list requires `_href`. Whether Simpro accepts
  `_href` as a `columns` value is unverified; if it does not, customer
  projections fail with a 422. `tests/test_live_contract.py` checks this in
  W1 T5.

## Decision

**Option 4** (recommended; Proposed until Alex accepts).

1. The mock adds nothing to a projection: `projection.project()` returns only
   the requested keys. This supersedes "`ID` is always included" in ADR-013 §5.
2. `simpro_client` adds the model's missing required fields to every `columns`
   projection, on `get()`, `fetch_page()` and `iter_all()`, after the caller's
   own columns.
3. Models stay contract-governed (ADR-013); no field becomes optional because
   of projections.

## Consequences

- A caller can name only the fields it needs. `src/simpro_client/CLAUDE.md`
  §9's caller rule is replaced by the client behaviour.
- The drift test that expected a narrow projection to raise
  (`test_projecting_away_a_required_field_fails_validation`) is replaced by one
  that expects it to validate.
- The mock's integration tests assert that no `ID` is added.
- Live check pending: `_href` as a column (W1 T5). If Simpro rejects it, the
  fix is to leave fields starting with `_` out of the added set and make
  `_href` optional on the list model, which needs a contract-deviation note.

## Revisit if

- Live checks show Simpro rejects a required field as a column.
- A consumer needs a projection without the required fields, for example a
  count-only query. It can then call the raw client.
