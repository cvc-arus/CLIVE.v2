# ADR-015: Simpro data access control model

- **Status:** Proposed
- **Date:** 2026-10-09
- **Deciders:** Alex
- **Related:** ADR-014 (Simpro access mechanism), ADR-016 (conversational access approach)

## Context

Multiple CVC users will query Simpro data through Open WebUI (Phase 3B).
Some data must be restricted for some users: by company (CVC Service vs
CVC Projects), by resource (e.g. Employees), by field (e.g. quote values) and
by row (e.g. only jobs assigned to the user).

Phase 3 authenticates to Simpro with OAuth2 Client Credentials, which gives the
backend a single service identity with no notion of the individual user.

Restrictions placed in prompts are not access control: a model can be talked
into revealing anything it has been given.

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

Storage: a dedicated `clive_gateway` database and least-privilege DB user on
the existing Phase 2 Postgres instance, rather than a new container. This keeps
hardware use down while isolating access by credentials. Schema: see the
Phase 3B PDD, section 7.2.

## Consequences

- An admin process for joiners, movers and leavers is required (admin guide).
- A build-time test ensures every `simpro_client` model field is either
  classified or recorded as reviewed, so new fields cannot silently become visible.
- The `clive_gateway` database must be added to the backup strategy.
- Field classifications must be re-validated against real Simpro payloads at switchover.

## Revisit if

- Live Simpro access is enabled and its per-user permission behaviour can be verified.
- Permission drift between CLIVE and Simpro becomes a recurring problem.
