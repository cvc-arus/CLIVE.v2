# ADR-014: Simpro data access control model

- **Status:** Proposed
- **Date:** 2026-10-09
- **Deciders:** Alex
- **Related:** ADR-009 (Phase 3 → Phase 4 handoff: `clive-gateway` as the single Simpro access point), ADR-015 (conversational access approach).
  ADR-009's `Related:` line cites this draft as "ADR-011 (Simpro data access control model, proposed)"; correcting it is pending Alex.

## Context

Multiple CVC users will query Simpro data through Open WebUI (Phase 3B).
Some data must be restricted for some users: by company (CVC Service vs
CVC Projects), by resource (e.g. Employees), by field (e.g. quote values) and
by row (e.g. only jobs assigned to the user).

Phase 3 authenticates to Simpro with OAuth2 Client Credentials, which gives the
backend a single service identity with no notion of the individual user.

Restrictions placed in prompts are not access control: a model can be talked
into revealing anything it has been given.

Simpro applies security groups to API applications as well as to users
(`docs/simpro/simpro-api-findings.md` §2.2), so Simpro itself can bound what
CLIVE's service identity can read.

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
- Con: how Simpro's API applies user permissions under this grant cannot be
  verified until live access is enabled.

## Decision

**Option 1**, behind a permission interface designed so it could later
delegate to per-user Simpro tokens.

Rules:
- Enforcement happens in `clive-gateway`, never in prompts or tools.
- Company and resource access are allow-lists; anything absent is denied.
- Row scope is `all` or `assigned` (filtered by the user's Simpro employee ID;
  denied if no ID is mapped).
- Sensitive fields are tagged with classifications (e.g. `financial`,
  `personal`) and hidden unless a role is granted that classification.
- A user's permissions are the union of their roles.
- Every request is audited (allow, deny, error).
- Service accounts (no human user) use the same model.
- CLIVE's roles operate inside a dedicated, read-only Simpro security group
  for CLIVE's API application, limited to the resources CLIVE needs. That
  group is the outer boundary: even a CLIVE bug cannot expose data it excludes.

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
> unchanged. This resolves the conflict only; the ADR itself is still Proposed.

## Consequences

- An admin process for joiners, movers and leavers is required (admin guide).
- A build-time test ensures every `simpro_client` model field is either
  classified or recorded as reviewed, so new fields cannot silently become visible.
- The `clive_gateway` database must be added to the backup strategy.
- Field classifications must be re-validated against real Simpro payloads at switchover.

## Revisit if

- Live Simpro access is enabled and its per-user permission behaviour can be verified.
- Sandbox testing can verify how Simpro applies security groups per user: that
  makes Option 2 more realistic and it should be re-evaluated then.
- Permission drift between CLIVE and Simpro becomes a recurring problem.
