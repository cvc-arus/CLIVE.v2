# PDD — Phase 3B: Simpro Conversational Access

| | |
|---|---|
| **Project** | CLIVE Enterprise AI Platform (CVC) |
| **Phase** | 3B — Simpro Conversational Access |
| **Version** | 0.1 (draft for approval) |
| **Date** | 2026-10-09 |
| **Owner** | Alex (Lead Engineer) |
| **Status** | Draft — awaiting approval |
| **Related ADRs** | ADR-009 (Phase 3 → Phase 4 handoff: `clive-gateway` as the single Simpro access point), ADR-010 (resilience policy), ADR-014 (access control model), ADR-015 (conversational access approach) |

---

## 1. Purpose

Allow any authorised CVC user to ask questions about Simpro data in Open WebUI
and receive accurate answers, with access restricted by role.

This requirement was not in the original scope (`docs/scope/clive-scope.md`) or
in Scope Revision 2 (`docs/scope/scope-rev2.md`). It was added in October 2026 after informal user research confirmed
it would help day-to-day work.

### Why "3B" and not a new phase number

Phases 4–10 are referenced across existing PDDs, ADRs and the roadmap.
Inserting a new number would force renumbering everywhere. "3B" places the
work after Phase 3 and before Phase 4, which is where its dependencies put it.

## 2. Business value

- **Faster answers.** Staff get one-off Simpro facts (open jobs at a site, last
  quote for a customer, assets installed) in seconds, without navigating Simpro
  or interrupting colleagues who know it well.
- **Cross-cutting questions.** Common questions that span screens or both
  companies (Service and Projects) become a single query instead of an export
  or a custom report.
- **Governed access.** Staff can be given *some* Simpro visibility without full
  Simpro access, with every request audited.
- **Reusable foundation.** The gateway, permission model and query catalogue
  become the access layer for Phase 4 (document generation) and Phases 6–9
  (agents). Part of this phase's cost would otherwise be spent later.

## 3. Objectives

1. A single, audited, permission-checked access point to Simpro data (`clive-gateway`).
2. A role-based access control model enforced server-side, deny by default.
3. An Open WebUI tool that lets the local LLM answer questions using a fixed
   catalogue of read-only queries.
4. The minimum security controls needed to expose this to multiple users on
   the LAN (brought forward from Phase 5).
5. A pilot with real users, and a handover to Phase 4.

## 4. Scope

### In scope

- `clive-gateway` FastAPI service (Docker Compose, single worker)
- `clive_gateway` database: access control tables and audit log (Alembic migrations)
- Policy engine: company, resource and row-scope checks; field masking by classification
- Query catalogue v1: 8–10 read-only, parameterised queries
- Open WebUI tool calling the gateway with the user's identity
- Service accounts for non-human callers (needed by Phase 4)
- Minimum security slice: Nginx + HTTPS, LAN-only firewall, Open WebUI hardening
- Model evaluation for tool calling within 10 GB VRAM
- User guide, admin guide (onboarding users and roles), updated architecture docs

### Non-goals

| Excluded | Reason / where it goes |
|---|---|
| Write operations (create/update in Simpro) | Read-only by design; revisit with a dedicated ADR |
| Per-user Simpro login (Authorization Code Grant) | Deferred (ADR-014 Option 2); revisit once live API behaviour can be verified |
| Free-form text-to-SQL | Rejected in ADR-015 |
| Embedding Simpro records in the vector store | Rejected in ADR-015; bypasses all access control |
| Response caching | Decided in Sprint 6 if the pilot shows a need (new ADR) |
| Access from outside the CVC network | Phase 5 (full security) |
| Document generation | Phase 4 |

## 5. Entry and exit criteria

**Entry criteria**
1. Phase 3 signed off. **Met:** Phase 3 closed 2026-10-09 (see `docs/roadmap.md`).
2. ADR-009's decision recorded (PR #44, 2026-10-09). **Met**; ADR-009
   accepted (Status line updated by Alex 2026-10-15).
3. Course correction sprint complete (`docs/course-correction-plan.md`;
   progress in `docs/STATUS.md`).

**Exit criteria**
1. All Phase 3B sprint acceptance criteria met.
2. Pilot completed with at least two users per role, feedback logged.
3. ADR-014 and ADR-015 accepted; caching ADR written if required.
4. Gateway query catalogue covers the resources Phase 4 needs, as listed in
   ADR-009's Consequences: Customers, Sites, Contacts, Jobs, Quotes, Projects,
   Assets, Employees. Simpro has no Projects resource: a project is a Job with
   `Type="Project"` (ADR-013), so Projects is a filtered Jobs query.
5. Phase 4 handover checklist signed off. This replaces the "Phase 4 readiness
   review" previously planned as Phase 3 Sprint 6.

## 6. Architecture

### 6.1 Components

| Component | New / existing | Notes |
|---|---|---|
| `open-webui` | Existing | Configuration changes only (groups, tool permissions, sharing off) |
| Simpro tool | New | Python tool inside Open WebUI; calls the gateway over HTTP |
| `clive-gateway` | New | FastAPI; the only runtime importer of `simpro_client` (ADR-009) |
| `clive_gateway` database | New | Dedicated database and DB user on the existing Phase 2 Postgres instance (ADR-014) |
| `simpro_client` | Existing | Unchanged; remains a pure Simpro library |
| `simpro-mock` / `simpro-mock-db` | Existing | Data source until live Simpro access is enabled |
| `ollama` | Existing | Model may change following the Sprint 1 evaluation |
| `nginx` | New | Reverse proxy with HTTPS in front of Open WebUI |

> **Conflict resolved (Alex, 2026-10-15).** Putting the `clive_gateway` database
> on the Phase 2 Postgres instance (ADR-014) conflicted with root `CLAUDE.md` §3,
> which kept the Phase 2 instance (`postgres`, port 5432) and the Phase 3
> instance (`simpro-mock-db`, port 5433) isolated. Alex kept the storage choice
> and narrowed §3: `clive-gateway` may use its own `clive_gateway` database
> there, through its own least-privilege DB user, but must never connect to the
> knowledge-base database, and no test may run against port 5432.

### 6.2 Component diagram

```
  Browser (CVC LAN, HTTPS)
          │
          ▼
  ┌──────────────┐
  │    nginx     │  TLS termination, only exposed entry point
  └──────┬───────┘
         ▼
  ┌──────────────┐      ┌──────────────┐
  │  open-webui  │◄────►│    ollama    │  local LLM, tool calling
  │ + Simpro tool│      └──────────────┘
  └──────┬───────┘
         │ HTTP (internal network only)
         │ service secret + user identity + correlation ID
         ▼
  ┌──────────────────────────────┐      ┌─────────────────────┐
  │        clive-gateway         │─────►│ clive_gateway DB    │
  │  policy · masking · audit    │      │ roles, rules, audit │
  │  imports simpro_client       │      └─────────────────────┘
  └──────────────┬───────────────┘
                 │ OAuth2 Client Credentials, rate limited (ADR-010)
                 ▼
  ┌──────────────────────────────┐
  │ Simpro API                   │
  │ now:   simpro-mock :8100     │
  │ later: {build}.simprosuite.com│
  └──────────────────────────────┘
```

### 6.3 Request data flow

1. User signs in to Open WebUI. The Simpro tool is visible only to permitted groups.
2. The LLM selects one query from the catalogue and supplies its arguments.
3. The tool calls `POST /v1/queries/{query_name}` on the gateway with the service
   secret, the user's identity and a correlation ID.
4. The gateway authenticates the caller (service secret), resolves the user to
   roles, and evaluates the policy. Anything not explicitly allowed is denied.
5. If allowed, the gateway calls Simpro via `simpro_client`, applying row filters
   where a role's scope is `assigned`.
6. The gateway removes classified fields the user's roles do not unlock,
   computes counts and totals in Python, and caps the rows returned.
7. The gateway writes an audit record (allow, deny or error).
8. The tool returns the summary to the LLM, which writes the answer. On denial,
   the LLM tells the user they lack access; it never receives the data.

## 7. Access control model (detail in ADR-014)

### 7.1 Principles

- Enforced in the gateway, never in prompts or in the tool.
- Deny by default at company and resource level.
- Classified fields hidden unless a role is explicitly granted the classification.
- Data is filtered before it reaches the LLM.
- Every request is audited.

### 7.2 Schema (`clive_gateway` database)

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Human users and service accounts | `id`, `account_type` (human/service), `openwebui_user_id`, `email`, `display_name`, `simpro_employee_id` (nullable), `is_active` |
| `roles` | Named roles | `id`, `name`, `description` |
| `user_roles` | Many-to-many user ↔ role | `user_id`, `role_id` |
| `role_companies` | Simpro companies a role may see | `role_id`, `company_id` (Service and Projects IDs from configuration) |
| `role_resources` | Resources a role may query, and row scope | `role_id`, `resource`, `scope` (`all` / `assigned`) |
| `classifications` | Sensitivity labels | `code` (e.g. `financial`, `personal`), `description` |
| `field_classifications` | Which model fields carry which label | `resource`, `field_name`, `classification` |
| `role_classification_grants` | Labels a role may see | `role_id`, `classification` |
| `audit_log` | One row per request | `occurred_at`, `correlation_id`, `user_email`, `query_name`, `parameters` (jsonb), `decision`, `deny_reason`, `result_count`, `duration_ms` |

A test fails the build if any `simpro_client` model field is neither classified
nor recorded as reviewed-and-unclassified, so new fields cannot silently become visible.

CVC's Simpro custom fields are readable through the API and may hold sensitive
data, so each one is added to the field classification list (classified or
reviewed-and-unclassified) before go-live (`docs/simpro/simpro-api-findings.md` §2.4).

Simpro company IDs are configuration, never constants. The mock uses `1`
(Service) and `2` (Projects); the real IDs are read from Simpro's
System > Setup > Company and set in configuration. No gateway code, seed data
or test outside the mock may assume `1` and `2` (`simpro-api-findings.md` §2.3).

### 7.3 Policy evaluation order

1. Caller authenticated (service secret)? Otherwise `401`.
2. User exists and is active? Otherwise deny.
3. Requested company in the user's roles' companies? Otherwise deny.
4. Requested resource in the user's roles' resources? Otherwise deny.
5. Scope: if every granting role has `assigned`, filter rows to the user's
   `simpro_employee_id`. If no employee ID is mapped, deny.
6. Mask classified fields not granted to any of the user's roles.
7. Audit.

Where a user holds several roles, permissions are the union of those roles.

### 7.4 Permission matrix (to be completed in Sprint 1)

Rows below are illustrative only and must be replaced with CVC's actual roles.

| Role | Companies | Resources | Scope | Classifications |
|---|---|---|---|---|
| *e.g. Engineer* | *Service* | *Jobs, Sites, Assets* | *assigned* | *none* |
| *e.g. Office/Admin* | *Service, Projects* | *Customers, Sites, Jobs, Contacts* | *all* | *personal* |
| *e.g. Management* | *Service, Projects* | *All* | *all* | *financial, personal* |
| `docgen` (service) | Service, Projects | Phase 4 needs | all | as Phase 4 requires |

## 8. Query catalogue v1 (candidate list)

To be finalised in Sprint 1 from the user research. Each query is read-only,
parameterised, and returns a compact summary rather than raw records.

| Query | Resource | Purpose |
|---|---|---|
| `find_customer` | Customers | Look up a customer by name |
| `customer_overview` | Customers, Sites, Jobs | Sites and open work for one customer |
| `list_jobs` | Jobs | Jobs filtered by company, status, site, date range |
| `get_job` | Jobs, Job Notes | Detail for one job |
| `my_jobs` | Jobs | Jobs assigned to the asking user |
| `list_quotes` | Quotes | Quotes filtered by customer, status, date range |
| `quote_summary` | Quotes | Counts and totals by status/period (financial) |
| `site_details` | Sites, Contacts | Site address and contacts |
| `site_assets` | Assets | Assets installed at a site |

## 9. Gateway API contract (v1)

- `POST /v1/queries/{query_name}` with a JSON body of query parameters.
- Headers: `Authorization: Bearer <service secret>`, `X-Clive-User` (Open WebUI
  user ID), `X-Clive-User-Email`, `X-Correlation-ID`.
- Success response envelope: `query`, `summary`, `data` (capped rows),
  `masked_fields`, `truncated`, `correlation_id`.
- Denied: `403` with `error: "forbidden"` and a user-safe `reason`.
- `GET /healthz` for health checks.
- The OpenAPI schema generated by FastAPI is the published contract; breaking
  changes need a new version path (ADR-009).
- The gateway port is reachable only on the internal Docker network.

## 10. Security requirements

- Only admins may create or edit Open WebUI tools. Tools run arbitrary Python,
  so a user who could write one could read the gateway secret and impersonate others.
- The gateway secret lives in `.env` and the tool's admin-only settings; never in prompts.
- Open WebUI: sign-ups disabled or admin-approved; chat sharing disabled;
  Simpro tool restricted to permitted groups.
- Nginx with HTTPS is the only exposed entry point; firewall restricts access to the CVC LAN.
- Gateway DB user has least privilege on `clive_gateway` only.
- Simpro data must never be written to the PGVector knowledge base.
- Audit log retention period to be agreed (open question).

## 11. Non-functional requirements

| Area | Requirement |
|---|---|
| Rate limiting | Gateway runs a single uvicorn worker so the ADR-010 limiter holds (8 req/sec) |
| Result size | Default cap of 50 rows returned to the LLM; summaries computed over the full result |
| Latency | Gateway p95 under 2 s per query against the mock (excluding LLM time) |
| Logging | JSON logs with correlation IDs, propagated from the tool to Simpro calls |
| Availability | Restart policy `unless-stopped`; health check on `/healthz` |
| Testing | Unit and integration tests run offline against `simpro-mock`, which stays the fast, deterministic default. Opt-in, read-only contract tests against CVC's live Simpro build (the environment type is in the private build notes; Alex, 2026-10-16) prove `simpro_client` models match the real API; differences found there are fixed in the mock. They are skipped by default, send only `GET`s and the token request, and print no client data (root `CLAUDE.md` §3 and §9; `docs/simpro/simpro-api-findings.md` §2.1) |
| Backups | `clive_gateway` database included in the backup script (`scripts/backup.sh` currently dumps only the Phase 2 `POSTGRES_DB`, so this needs a change; see W5) |

## 12. Sprint plan

Each sprint ends with passing tests, documentation updates and a git commit.

### Sprint 1 — Decisions and design (week 1)
- ADR-009 already decided (PR #44); accept ADR-014 and ADR-015.
- Complete the permission matrix with CVC stakeholders.
- Finalise query catalogue v1 from the user research.
- Model spike: evaluate 2–3 tool-calling models that fit in 10 GB VRAM against
  the course correction W4 evaluation set
  (`docs/sprints/course-correction/W4-evaluation.md`; not built yet).

**Acceptance:** ADRs accepted; matrix and catalogue signed off; model chosen
with recorded test results.

### Sprint 2 — Minimum security slice (week 2)
- Nginx reverse proxy with HTTPS in front of Open WebUI.
- Firewall rules: LAN-only access; Open WebUI port no longer directly exposed.
- Open WebUI: sign-up policy, user groups, admin-only tool creation, chat sharing off.

**Acceptance:** Open WebUI reachable only via HTTPS on the LAN; a non-admin
cannot create tools; groups exist matching the permission matrix.

### Sprint 3 — Gateway foundation (weeks 3–4)
- `clive-gateway` service scaffold and Docker Compose service (single worker).
- `clive_gateway` database, DB user and Alembic migrations.
- Service-secret authentication, policy engine, field masking, audit logging.
- Seed roles and permissions from the matrix.

**Acceptance:** policy unit tests cover every evaluation step including deny
paths; audit rows written for allow, deny and error; migrations reversible.

### Sprint 4 — Query catalogue v1 (weeks 5–6)
- Implement catalogue queries on `simpro_client` against the mock.
- Aggregations in Python; row caps; response envelope.
- Field-classification completeness test.
- Permission tests: every role × every query.

**Acceptance:** all catalogue queries pass integration tests against the mock;
the role × query matrix test passes; no unclassified, unreviewed fields.

### Sprint 5 — Open WebUI integration (week 7)
- Simpro tool calling the gateway with user identity and correlation ID.
- Tool settings (gateway URL, secret) admin-only; tool restricted by group.
- Chosen model and system prompt configured.
- End-to-end tests with one test account per role, including denial responses.

**Acceptance:** each test account receives correct answers within its
permissions and a clear refusal outside them; audit log matches the test run.

### Sprint 6 — Pilot and hardening (weeks 8–9)
- Pilot with at least two users per role; log unsupported questions for v2.
- Concurrency and rate-limit check.
- Caching decision (new ADR if needed).
- User guide, admin guide, architecture and security docs updated.
- Phase 4 handover checklist.

**Acceptance:** pilot feedback recorded; exit criteria in section 5 met.

## 13. Schedule

Assumes full-time effort from Phase 3 sign-off. Scale up if shared with other duties.

| Weeks | Sprint |
|---|---|
| 1 | Sprint 1 — Decisions and design |
| 2 | Sprint 2 — Minimum security slice |
| 3–4 | Sprint 3 — Gateway foundation |
| 5–6 | Sprint 4 — Query catalogue v1 |
| 7 | Sprint 5 — Open WebUI integration |
| 8–9 | Sprint 6 — Pilot and hardening |

Working Q&A on mock data from about week 7. When live Simpro access is enabled,
allow 2–3 days to re-validate field classifications against real payloads.

## 14. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| No local model handles tool calls reliably within 10 GB VRAM | Wrong or failed answers; loss of trust | Sprint 1 spike; small, well-described catalogue; computation in code; fallback to simpler single-tool design |
| Live Simpro access delayed | Feature runs on mock data only | Build and pilot on mock; switchover is a configuration change |
| Real payloads differ from the mock | Masking or queries break | Re-validate classifications at switchover; `extra="ignore"` models |
| Shared Simpro rate limit exhausted by chat usage | Other Simpro integrations throttled | Single gateway worker; conservative limit; caching ADR if pilot shows pressure |
| Permission matrix drifts from staff roles in Simpro | Over- or under-exposure | Admin guide with a joiner/mover/leaver process; periodic review |
| Tool misuse or secret leakage | Impersonation | Admin-only tool creation; secret only in `.env` and admin settings |
| Concurrent users on one GPU | Slow responses at busy times | Set expectations in pilot; future hardware upgrade |
| Phase 4 delayed by ~9 weeks | Document generation later | Phase 4 reuses the gateway, reducing its own scope |

## 15. Open questions

1. Which CVC roles use this, and what should each see? (Sprint 1 blocker)
2. Audit log retention period.
3. Certificate approach for HTTPS on the LAN (internal CA vs self-signed).
4. Which users map to Simpro employee IDs for `assigned` scope, and who maintains it.
