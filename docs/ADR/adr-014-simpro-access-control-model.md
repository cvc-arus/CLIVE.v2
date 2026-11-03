# ADR-014: Simpro data access control model

- **Status:** **Accepted** — 2026-11-03 (Alex). Proposed 2026-10-09
- **Date:** 2026-10-09; updated 2026-10-17 (Claude, at Alex's request) for live
  Simpro access: no dedicated security group, only the two configured
  companies, customers and sites shared across companies. Build-specific
  values moved to the private build notes 2026-10-19 (ADR-017). Revised
  2026-11-03 (Alex), before acceptance: no per-user company permissions,
  because every CVC employee may see both companies
- **Deciders:** Alex
- **Related:** ADR-009 (Phase 3 → Phase 4 handoff: `clive-gateway` as the single Simpro access point), ADR-015 (conversational access approach, accepted 2026-11-03).

## Context

Multiple CVC users will query Simpro data through Open WebUI (Phase 3B).
Some data must be restricted for some users: by resource (e.g. Employees),
by field (e.g. quote values) and by row (e.g. only jobs assigned to the user).

**Company access is not restricted per user (Alex, 2026-11-03).** Every CVC
employee has access to the information of both companies CLIVE uses, Service
and Projects. CLIVE therefore has no per-user or per-role company permission.

Phase 3 authenticates to Simpro with OAuth2 Client Credentials, which gives the
backend a single service identity with no notion of the individual user.

Restrictions placed in prompts are not access control: a model can be talked
into revealing anything it has been given.

**Live access (2026-10-16, Alex).** CLIVE has OAuth2 Client Credentials access
to CVC's own build and uses it read-only (root `CLAUDE.md` §3). Contrary to
the plan when this ADR was drafted, there is no dedicated read-only security
group for the API application (`docs/simpro/simpro-api-findings.md` §2.2; its
permissions are in the private build notes, ADR-017). CLIVE therefore does not
rely on Simpro to bound what its service identity can read or write. The only
limits it relies on are its own: the GET-only client and the access control
this ADR decides.

What the first live check (2026-10-17, `docs/simpro/mock-vs-public-api.md` §6)
means for access control:
- The build has more companies than CLIVE uses. CLIVE uses only the two
  configured ones, **Service** and **Projects** (`SIMPRO_COMPANY_ID_SERVICE`,
  `SIMPRO_COMPANY_ID_PROJECTS`; Alex, 2026-10-17). Listing `/companies/` is
  allowed, but no request is ever sent to a route scoped to any other company.
- **Customers and sites are build-wide, not per company.** They return
  identical totals under both companies. Jobs, quotes and employees differ
  per company. Since every user may see both companies, this no longer
  affects access control; it matters only so that results queried under both
  companies are not double-counted.

## Options considered

### Option 1 — Shared service account + CLIVE-managed roles
Keep Client Credentials. `clive-gateway` maps each user to roles stored in its
own database and filters data before it reaches the LLM.
- Pro: works with the existing Phase 3 code; fully buildable and testable on the mock.
- Pro: explicit, testable, auditable rules.
- Con: permissions maintained separately from Simpro; risk of drift as staff change roles.
- Con: row-level rules need a maintained user → Simpro employee ID mapping.

### Option 2 — Per-user Simpro login (Authorization Code Grant)
Each user signs in to Simpro; queries run with their own token.
- Pro: Simpro is the single source of truth for permissions.
- Con: mock must implement the login flow and per-user permissions.
- Con: per-user refresh tokens must be stored, breaking the "tokens in memory only" rule.
- Con: OAuth redirects inside Open WebUI tools are awkward.
- Con: how Simpro's API applies user permissions under this grant is still
  unverified. Live access is Client Credentials only, so testing this needs
  an Authorization Code application and a test user (not available,
  2026-10-17).

## Decision

**Accepted: Option 1** (Alex, 2026-11-03), behind a permission interface designed so it could later
delegate to per-user Simpro tokens.

Rules:
- Enforcement happens in `clive-gateway`, never in prompts or tools.
- Resource access is an allow-list; anything absent is denied.
- **No per-user company permissions** (Alex, 2026-11-03). Every active user
  may see both configured companies, Service and Projects. Company is a
  system rule, not a role setting: the gateway accepts only
  `SIMPRO_COMPANY_ID_SERVICE` and `SIMPRO_COMPANY_ID_PROJECTS` and rejects
  any other company ID before calling Simpro, for every user and service
  account.
- Row scope is `all` or `assigned` (filtered by the user's Simpro employee ID;
  denied if no ID is mapped).
- Sensitive fields are tagged with classifications (e.g. `financial`,
  `personal`) and hidden unless a role is granted that classification.
- A user's permissions are the union of their roles.
- Every request is audited (allow, deny, error).
- Service accounts (no human user) use the same model.
- ~~CLIVE's roles operate inside a dedicated, read-only Simpro security group
  for CLIVE's API application, limited to the resources CLIVE needs.~~
  **Not available (2026-10-16):** no such group was set up, so CLIVE treats
  Simpro as providing no outer boundary. `clive-gateway` is the only boundary on what
  CLIVE reads, and the GET-only client is the only guard against writes. The
  gateway must therefore expose only its fixed query catalogue (ADR-015) and
  never pass raw paths or arbitrary company IDs through to Simpro.

Storage: a dedicated `clive_gateway` database and least-privilege DB user on
the existing Phase 2 Postgres instance, rather than a new container. This keeps
hardware use down while isolating access by credentials. Schema: see the
Phase 3B PDD, section 7.2.

> **Conflict resolved (Alex, 2026-10-15).** Placing `clive_gateway` on the
> Phase 2 Postgres instance (`postgres`, port 5432) conflicted with root
> `CLAUDE.md` §3, which kept that instance off-limits to Phase 3 code and
> tests (recorded 2026-10-13). Alex kept this storage choice and narrowed §3
> instead: `clive-gateway` may use its own `clive_gateway` database there,
> through its own least-privilege DB user. It must never connect to the
> knowledge-base database, and no test may run against port 5432, so the
> gateway's tests need a disposable database. The decision text above is
> unchanged. This resolved the conflict only; Alex accepted the ADR on
> 2026-11-03.

## Consequences

- An admin process for joiners, movers and leavers is required (admin guide).
- A build-time test ensures every `simpro_client` model field is either
  classified or recorded as reviewed, so new fields cannot silently become visible.
- The `clive_gateway` database must be added to the backup strategy.
- Field classifications must be validated against real Simpro payloads. Live
  access makes that possible now, but under root `CLAUDE.md` §9 Claude Code
  sees field names only, and Alex checks the values.
- Treat the client secret as able to write to Simpro: it stays in `.env`
  only, it is rotated if exposed, and the gateway is the only runtime holder
  (ADR-009). See the Simpro-permissions risk in `docs/STATUS.md`.

## Revisit if

- An Authorization Code application and a test user become available, so
  read-only checks can verify how Simpro applies security groups per user.
  That makes Option 2 more realistic and it should be re-evaluated then.
  (Live Client Credentials access, the original trigger, arrived 2026-10-16
  but cannot answer this question.)
- Simpro offers a read-only or restricted security group for API
  applications. The outer boundary in the Decision would then be restored.
- Permission drift between CLIVE and Simpro becomes a recurring problem.
- CVC needs some users kept out of one company's data. A per-role company
  allow-list would then be added by a superseding ADR.
