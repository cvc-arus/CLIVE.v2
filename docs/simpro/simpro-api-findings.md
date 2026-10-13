# Simpro API — Findings from the Simpro Representative

**Received:** October 2026 · **Recorded:** 2026-10-12
**Source:** written answer from the Simpro representative to CVC's questions.
Items marked *unverified* must be confirmed via Support case or sandbox testing.

## 1. Summary of what Simpro told us

| Topic | Answer | Confidence |
|---|---|---|
| Cost | API stated to be free; CVC still awaiting price and access level | Commercial answer pending |
| Registration | Applications created in Simpro Premium: System > Setup > System Setup > API > Applications. Name, description, Redirect URI, authentication method (API Key or OAuth2). | Stated |
| Admin permissions | Managing API applications needs the *Company Management* and *API Applications* security group permissions | Stated |
| Provisioning lead time | Not specified | Unknown |
| Access scoping | API credentials operate within the Security Group boundaries of the authenticating user/application | Stated; application-level read-only scoping *unverified* |
| Field restrictions | Custom fields can be set Read Only or locked via the API | Stated |
| Multi-company | Company IDs listed under System > Setup > Company; single-company builds use 0 | Stated |
| Cross-company calls with one credential | Not confirmed | *Unverified* — Support case |
| Sandbox | Free shared sandbox (no live data) for API testing, requested by Support case | Stated |
| UAT build | Dedicated UAT build via Operations: minimum one user licence per month, possible migration fees | Stated |
| Authentication | OAuth2 or API Key | Stated |
| Rate limits | HTTP 429 on throttling; exact limits, `Retry-After` and token TTL not specified | Unknown |
| Documentation | Public: https://developer.simprogroup.com/apidoc/ · in-product: Settings > System Setup > API > Documentation | Stated |
| Build-specific OpenAPI/Swagger export | Available via Support case | Stated |
| Custom fields | Readable via the API | Stated |
| Webhooks | Job Created/Updated, Quote Created/Updated; configured under API > Webhook Subscriptions; logs under API > Webhook Logs | Stated |
| Authorization Code ("Log in with Simpro") | Redirect URIs registered under System Setup > API > Applications | Stated |

## 2. Implications for CLIVE

### 2.1 Sandbox changes the testing strategy

The mock was built because there was no way to test against real Simpro. The
shared sandbox removes that gap for **response shape and behaviour** (not for
CVC's own data or configuration).

- Mock stays: fast, offline, deterministic tests and local development.
- Sandbox adds: contract tests proving `simpro_client` models match the real API.
- Mock scope is frozen; differences found against the sandbox are fixed in the mock.
- Running anything against the sandbox needs Alex's approval of an exception to
  root `CLAUDE.md` §3, which says code and tests must never contact `*.simprosuite.com`.

### 2.2 Security groups are the outer permission boundary

Create a dedicated Simpro security group for CLIVE's API application with
read-only access to only the resources CLIVE needs. CLIVE's own roles (ADR-014)
then restrict further inside that boundary. Even a CLIVE bug cannot expose data
the security group excludes.

This also makes ADR-014 Option 2 (per-user Simpro login) more realistic, since
Simpro applies security groups per user. Keep Option 1 for now; revisit once
the sandbox lets the behaviour be verified.

### 2.3 Company IDs are configuration

The mock uses `company_id=1` (Service) and `2` (Projects). Real IDs must be read
from System > Setup > Company and set in configuration. Nothing may assume 1 and 2.

### 2.4 Custom fields need classification

CVC's custom fields are readable via the API. They must be added to the Phase 3B
field classification list (ADR-014) before go-live, as they may hold sensitive data.

### 2.5 Rate limits and token lifetime remain unknown

Keep ADR-010's conservative defaults (8 req/sec, backoff with jitter on 429,
proactive token refresh and refresh on 401), with every retry delay, including a
server-supplied `Retry-After`, capped by `SIMPRO_MAX_RETRY_DELAY` (ADR-012). Measure on the sandbox where possible.

### 2.6 Webhooks: future option, not current scope

Job and quote webhooks could keep a cache fresh instead of polling. However,
Simpro (cloud) would need to reach a CLIVE endpoint, which conflicts with the
LAN-only design. Any use needs its own ADR and Phase 5 security work.

## 3. Support cases to raise

| # | Request | Why | Priority |
|---|---|---|---|
| 1 | Access to the shared API sandbox | Contract-test `simpro_client` against the real API | High — raise first |
| 2 | Build-specific OpenAPI/Swagger export for CVC's build | Validate models against CVC's configuration, including custom fields. The generic published spec is already vendored (`docs/contracts/simpro-openapi-v1-get-subset.json`, ADR-013) | High |
| 3 | Can one OAuth2 Client Credentials application call both companies, and how is company context selected? | Gateway design for two companies | Medium |
| 4 | Can an API application be restricted to read-only, per resource, at application level? | Least-privilege setup (2.2) | Medium |
| 5 | Rate limits per build, `Retry-After` behaviour, access token lifetime | Tune ADR-010 settings | Low |

Record case numbers and answers in this file under section 4.

## 4. Support case log

| # | Case number | Raised | Answer | Date |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

## 5. Production setup checklist (when access is granted)

- [ ] Confirm the subscription includes API Applications
- [ ] Create a dedicated security group for CLIVE, read-only, minimum resources
- [ ] Create the API application (OAuth2, Client Credentials) under that group
- [ ] Store client ID and secret in `.env` only
- [ ] Record Company IDs for CVC Service and CVC Projects in configuration
- [ ] List custom fields and classify them (ADR-014)
- [ ] Run a read-only smoke check against <ENVIRONMENT_TYPE>, only with Alex's explicit approval (see root `CLAUDE.md` §3)
- [ ] Switch `SIMPRO_BASE_URL` and `SIMPRO_TOKEN_URL`
