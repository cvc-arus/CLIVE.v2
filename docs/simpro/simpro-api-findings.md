# Simpro API — Findings from the Simpro Representative

**Received:** October 2026 · **Recorded:** 2026-10-12 · **Updated:** 2026-10-16
with Alex's answers after live API access arrived
**Source:** written answer from the Simpro representative to CVC's questions,
and Alex's own setup of the API application (2026-10-16).
Items marked *unverified* are confirmed by read-only checks against the live
API (course correction W1 T5). the environment type is in the private build notes.

## 1. Summary of what Simpro told us

| Topic | Answer | Confidence |
|---|---|---|
| Cost | Free | Resolved (Alex, 2026-10-16) |
| Registration | Applications created in Simpro Premium: System > Setup > System Setup > API > Applications. Name, description, Redirect URI, authentication method (API Key or OAuth2) | Done: CVC's application exists and works (Alex checked it with Postman, 2026-10-16) |
| Admin permissions | Managing API applications needs the *Company Management* and *API Applications* security group permissions | Started; Alex has not found where these are set |
| Provisioning lead time | Not specified | Moot: access arrived 2026-10-16 |
| Access scoping | API credentials operate within the Security Group boundaries of the authenticating user/application | Stated. CVC's application has **<APP_PERMISSION_LEVEL> access** (§2.2); application-level read-only scoping *unverified* |
| Field restrictions | Custom fields can be set Read Only or locked via the API | Stated |
| Multi-company | Company IDs listed under System > Setup > Company; single-company builds use 0 | CVC: **Service <company-id>, Projects <company-id>**. The build also lists 0 and <company-id> (live check 2026-10-17); **only <company-id> and <company-id> are ever used** (Alex, 2026-10-17) |
| Cross-company calls with one credential | One credential calls both companies; the company is selected by the company ID in the path | Answered by Alex |
| Sandbox | Free shared sandbox (no live data) offered via Support case | **Not used** (Alex, 2026-10-16): CLIVE works against the live build, read-only |
| UAT build | Dedicated UAT build via Operations: minimum one user licence per month, possible migration fees | Stated; not used |
| Authentication | OAuth2 Client Credentials | Resolved: CVC's application uses OAuth2 (API Key not used) |
| Rate limits | HTTP 429 on throttling; the public docs give 10 requests per second per build (`docs/simpro/mock-vs-public-api.md` item 10); `Retry-After` not specified | Partly documented; to measure (§2.5) |
| Token lifetime | `expires_in: 3600`; a new token invalidates the old one (`docs/simpro/mock-vs-public-api.md` items 14–15) | Documented; to confirm live |
| Documentation | Public: https://developer.simprogroup.com/apidoc/ (Client Credentials workflow: https://developer.simprogroup.com/apidoc/?page=3366d2ea7906f693b27d57ed9cca3acb#tag/Client-credentials-grant-workflow) · in-product: Settings > System Setup > API > Documentation | Stated |
| Build-specific OpenAPI/Swagger export | Available via Support case | Stated; not requested |
| Custom fields | Readable via the API; documented at https://developer.simprogroup.com/apidoc/?page=07adc9c3c19b7c17e7309e86c22161a2#tag/ | Stated |
| Webhooks | Job Created/Updated, Quote Created/Updated; configured under API > Webhook Subscriptions; logs under API > Webhook Logs | Stated |
| Authorization Code ("Log in with Simpro") | Redirect URIs registered under System Setup > API > Applications | Stated |

## 2. Implications for CLIVE

### 2.1 Live, read-only testing (<ENVIRONMENT_TYPE>)

The mock was built because there was no way to test against real Simpro. Live
access to CVC's own build removes that gap, for response shape and behaviour
and for CVC's own data and configuration. Alex decided on 2026-10-16 not to use
the shared sandbox.

- Mock stays: fast, offline, deterministic tests and local development.
- Live adds: opt-in contract tests proving `simpro_client` models match the
  real API (W1 T3, run in T5). They are skipped by default.
  `tests/test_live_contract.py` covers `/companies/` (unpaginated, both
  companies present), the `Result-*` headers and model validation on
  customers, sites, jobs, quotes and employees in companies <company-id> and <company-id>, a job
  detail (empty dates), a projection without `ID`, and token reuse across two
  clients (`mock-vs-public-api.md` §5 items 1, 2, 4, 13, 15, 17). Run only when
  Alex asks, with the live settings in `.env`
  (`SIMPRO_COMPANY_ID_SERVICE=<company-id>`, `SIMPRO_COMPANY_ID_PROJECTS=<company-id>`, or the
  tests skip):

  ```bash
  SIMPRO_LIVE_TESTS=1 uv run pytest -m live -v --tb=no -rN
  ```

  `--tb=no -rN` keeps tracebacks and the short summary out of the output,
  since Pydantic and exception messages can echo values or the build host.
- **Read-only:** only `GET` requests and the OAuth2 token request; nothing is
  ever written to Simpro (root `CLAUDE.md` §3).
- **No client data reaches Claude Code:** live checks print status codes,
  counts, field and header names, and pass/fail only (root `CLAUDE.md` §9).
- Mock scope is frozen; differences found against live Simpro are fixed in the mock.

### 2.2 Security groups: the application has <APP_PERMISSION_LEVEL> access

The plan was a dedicated Simpro security group for CLIVE's API application,
read-only and limited to the resources CLIVE needs. Alex found this not needed:
the API application has <APP_PERMISSION_LEVEL> access, and the documentation on security groups
pointed the wrong way (2026-10-16).

Consequence: Simpro does not stop CLIVE writing or reading anything. The only
guards against a write are the read-only rule (root `CLAUDE.md` §3) and
`simpro_client`'s GET-only endpoints; the only guard on which data CLIVE sees is
CLIVE's own access control (ADR-014). A leaked client secret has <APP_PERMISSION_LEVEL> reach.
This is recorded as an open risk in `docs/STATUS.md`.

ADR-014 Option 2 (per-user Simpro login) relies on Simpro applying security
groups per user. Keep Option 1 for now; revisit once live checks show how
Simpro applies them.

### 2.3 Company IDs are configuration

The mock uses `company_id=1` (Service) and `2` (Projects). CVC's real IDs are
**<company-id> (Service)** and **<company-id> (Projects)** (Alex, 2026-10-16), set in configuration
(`SIMPRO_COMPANY_ID_SERVICE`, `SIMPRO_COMPANY_ID_PROJECTS`). Live `/companies/`
also returns 0 and <company-id>; **only <company-id> and <company-id> are ever used** (Alex, 2026-10-17), so
code must not iterate `/companies/` to discover companies. Nothing may assume
1 and 2.

Customers and sites are build-wide: both companies report the same totals
(<COUNT> customers, <COUNT> sites on 2026-10-17), while jobs, quotes and employees
differ. Counts of customers or sites must not be added across companies
(`docs/simpro/mock-vs-public-api.md` §6, item 19).

### 2.4 Custom fields need classification

CVC's custom fields are readable via the API. They must be added to the Phase 3B
field classification list (ADR-014) before go-live, as they may hold sensitive data.

### 2.5 Rate limits and token lifetime: to measure

Keep ADR-010's conservative defaults (8 req/sec, backoff with jitter on 429,
proactive token refresh and refresh on 401), with every retry delay, including a
server-supplied `Retry-After`, capped by `SIMPRO_MAX_RETRY_DELAY` (ADR-012).
Confirm against the live API (W1 T5) without deliberately exceeding the limit.

### 2.6 Webhooks: future option, not current scope

Job and quote webhooks could keep a cache fresh instead of polling. However,
Simpro (cloud) would need to reach a CLIVE endpoint, which conflicts with the
LAN-only design. Any use needs its own ADR and Phase 5 security work.

## 3. Support cases

W1 T1 (raise the cases) is **not needed** (Alex, 2026-10-16). Answers as known:

| # | Question | Why | Answer |
|---|---|---|---|
| 1 | Access to the shared API sandbox | Contract-test `simpro_client` against the real API | Not needed: live access, <ENVIRONMENT_TYPE> |
| 2 | Build-specific OpenAPI/Swagger export for CVC's build | Validate models against CVC's configuration, including custom fields. The generic published spec is already vendored (`docs/contracts/simpro-openapi-v1-get-subset.json`, ADR-013) | Not requested |
| 3 | Can one OAuth2 Client Credentials application call both companies, and how is company context selected? | Gateway design for two companies | Yes, by the company ID in the path (Alex) |
| 4 | Can an API application be restricted to read-only, per resource, at application level? | Least-privilege setup (2.2) | Not known (Alex); CVC's application has <APP_PERMISSION_LEVEL> access |
| 5 | Rate limits per build, `Retry-After` behaviour, access token lifetime | Tune ADR-010 settings | Partly documented (§1); to measure live |

## 4. Support case log

No cases raised (§3).

## 5. Production setup checklist

- [x] Confirm the subscription includes API Applications — API access enabled (Alex)
- [ ] ~~Create a dedicated security group for CLIVE, read-only, minimum resources~~ — not done: the application has <APP_PERMISSION_LEVEL> access (§2.2)
- [x] Create the API application (OAuth2, Client Credentials) — works, checked with Postman (Alex)
- [x] Store client ID and secret in `.env` only — done (Alex)
- [x] Record Company IDs for CVC Service and CVC Projects — <company-id> and <company-id> (Alex)
- [ ] List custom fields and classify them (ADR-014)
- [x] Run a read-only smoke check against <ENVIRONMENT_TYPE> — approved by Alex 2026-10-16, run 2026-10-17: authentication and every GET probed worked; three differences break the client (`docs/simpro/mock-vs-public-api.md` §6)
- [ ] Switch `SIMPRO_BASE_URL` and `SIMPRO_TOKEN_URL` — live values are in `.env` (Alex); no code or test reads them by default (§6)

## 6. Credentials as delivered vs CLIVE configuration

Simpro delivered the credentials in this form (placeholders, not the real
values):

```text
Type: Client Credentials
Token URL: https://<build>.simprosuite.com/oauth2/token
client_id: <client id>
client_secret: <client secret>
grant_type: client_credentials
```

They map onto `simpro_client`'s settings (`src/simpro_client/config.py`,
prefix `SIMPRO_`; names as in `.env.example`):

| Delivered | `.env` variable | Value |
|---|---|---|
| Token URL | `SIMPRO_TOKEN_URL` | `https://<build>.simprosuite.com/oauth2/token`, as delivered |
| — (not delivered) | `SIMPRO_BASE_URL` | `https://<build>.simprosuite.com/api/v1.0`: same host as the token URL, with the API path the client and mock use |
| client_id | `SIMPRO_CLIENT_ID` | as delivered |
| client_secret | `SIMPRO_CLIENT_SECRET` | as delivered |
| Type: Client Credentials | `SIMPRO_AUTH_MODE` | `client_credentials` |
| grant_type | — | not configurable: `src/simpro_client/auth.py` always sends `client_credentials` |
| — | `SIMPRO_COMPANY_ID_SERVICE`, `SIMPRO_COMPANY_ID_PROJECTS` | `<company-id>`, `<company-id>` (§2.3) |

Two differences from Simpro's documented token request (`docs/simpro/mock-vs-public-api.md` items 13 and 15):

- Simpro's docs show the token request as JSON; `auth.py` sends it
  form-encoded, with `client_id` and `client_secret` in the body. **Settled
  2026-10-17:** the live smoke check authenticated with the form-encoded request.
- A new token invalidates the old one, so `.env`'s credentials should be used
  by one `SimproClient` at a time (for example, not by a live test run while
  `clive-gateway` is running).

Every test builds its own settings pointing at the mock or at `respx`
(`tests/conftest.py`, `tests/test_client_mock_drift.py`), so live values in
`.env` do not make the default test run contact Simpro. Only code that calls
`get_settings()` or `SimproClient()` without settings reads them.
