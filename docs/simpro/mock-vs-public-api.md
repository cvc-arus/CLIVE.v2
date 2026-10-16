# Mock vs Simpro's Public API — What the Spec Cannot Settle

**Written:** 2026-10-16 (course correction W1 T2) at commit `fedbd8a`.
**Scope:** the points ADR-013's conformance work could not settle from the
published response schemas: the four mock behaviours listed as unverifiable in
`docs/roadmap.md`, error responses, and authentication details found on the way.
Field names, types and optionality are **not** covered here; they are governed
by `docs/contracts/simpro-openapi-v1-get-subset.json` and proved by
`tests/test_spec_conformance.py` (ADR-013).

No mock or client code was changed by this task.

## 1. Sources

| Source | What it is | Used for |
|---|---|---|
| Simpro's published OpenAPI 2.0 spec (`swagger.json`, 26,945,624 bytes, dated 2026-08-20, downloaded by Alex; ADR-013) | Full spec, 719 paths. Its 50 `x-traitTag` tags carry the prose of the public documentation (Pagination, Understanding errors, Customise displayed columns, API Call Limits, the grant workflows, and so on) | Every "Docs say" cell below quotes or summarises this prose or the spec's response declarations |
| `docs/contracts/simpro-openapi-v1-get-subset.json` | The vendored 25-path GET subset (ADR-013) | Parameters and declared responses of the routes CLIVE uses |
| https://developer.simprogroup.com/apidoc/ | The public portal | Not re-fetched: it returned HTTP 403 to this environment (ADR-013). The spec's documentation tags are the portal's source text |

The full spec declares **no response headers** on any of its 719 paths, and on
GET operations only `200` (704 operations) and `404` (331). No `400`, `401`,
`403`, `429` or `5xx` response is declared anywhere. Everything below about
those comes from the prose, or is "not stated".

Severity, per W1 T2:

- **Breaks client:** the mock behaves differently from documented Simpro in a
  way that makes `simpro_client` fail or return wrong data against real Simpro.
- **Cosmetic:** a documented or likely difference that `simpro_client` does
  not depend on.
- **Unknown:** the documentation does not settle it; needs the sandbox
  (W1 T5) or a Support case (`simpro-api-findings.md` §3). The "If the mock is
  wrong" column says what would break.
- **Match:** documented, and the mock and client already agree with it.

## 2. The four behaviours ADR-013 left unverified

| # | Behaviour | Docs say | Mock | Client | If the mock is wrong | Severity |
|---|---|---|---|---|---|---|
| 1 | `ID` in a `columns` projection that did not ask for it | **Not stated.** The only example (Customise displayed columns) requests `columns=ID,BillingAddress`, so it includes `ID` explicitly | Always adds `ID` (`projection.py`, `ALWAYS_INCLUDED`) | Every model requires `ID` (`id: int = Field(alias="ID")`) | A caller passing `columns` without `ID` gets a validation error from the client. Workaround needing no code change: always list `ID` | Unknown |
| 2 | `Result-Total` / `Result-Count` / `Result-Pages` headers | **Stated** (Pagination): listings return all three, e.g. `Result-Total: 10666`, `Result-Pages: 356`, `Result-Count: 30`. Default page size 30, `pageSize` up to 250 | Sets all three on collection routes; `pageSize` default 30, maximum 250 | Requires all three; `MAX_PAGE_SIZE = 250`, `DEFAULT_PAGE_SIZE = 30` | — | Match |
| 3 | `limit`'s exact semantics | **Not stated** beyond the parameter text "Set the limit of number of records in a request". The Pagination prose does not mention it | Narrows `pageSize` to `min(pageSize, limit)` (`middleware.py`, `paginate_query`) | Never sends `limit` | Only mock behaviour changes; the client is unaffected | Cosmetic |
| 4 | `/companies/` paginated or not | **Not settled.** The contract documents no `page`, `pageSize` or `limit` on `/companies/`; the List resources example shows a bare array with no headers. The Pagination prose says generally that "when you retrieve a listing, only the first 30 results are shown" | Paginates it like every other collection, with `Result-*` headers | Pages it, and raises `SimproProtocolError` when `Result-Pages` is missing | If upstream sends no `Result-*` headers on `/companies/`, the client's companies listing fails on every call | Unknown |

## 3. Error responses

| # | Case | Docs say | Mock | Client | Severity |
|---|---|---|---|---|---|
| 5 | Resource not found (`404`) | **Stated** (Understanding errors; `404` declared on 12 of the subset's detail routes): body `{"errors": [{"path": null, "message": "Individual customer not found.", "value": null}]}`, messages as in the contract (e.g. "Job not found.") | `404` with FastAPI's `{"detail": "Job not found"}`; some messages differ ("Customer not found" for both customer types) | Maps `404` to `SimproNotFoundError` and keeps the body as text without parsing it | Cosmetic |
| 6 | Missing or invalid token (`401`) | **Not stated**: no status or body documented | `401` with `{"detail": "Missing Bearer token"}` or `{"detail": "Invalid access token"}` | Invalidates the token and retries once (ADR-012), then raises | Unknown |
| 7 | Access denied by the Simpro security group (`403`) | **Not stated** | Never returns `403` | Raises `SimproClientError` | Unknown. Matters for the dedicated read-only security group (`simpro-api-findings.md` §2.2, ADR-014): what CLIVE sees when the group excludes a resource is untested |
| 8 | Out-of-range `page` / `pageSize` | **Not stated** (the parameters declare `minimum: 1`, `maximum: 250`) | FastAPI `422` with `{"detail": [...]}` | Raises `ValueError` before sending, so it never sends one | Cosmetic |
| 9 | Unknown filter field or unorderable `orderby` field | **Not stated** | `400` with `{"detail": ...}` naming the field (ADR-013 decision) | Raises `SimproClientError` | Unknown |
| 10 | Rate limiting (`429`) | **Stated** (API Call Limits): more than 10 requests per second to one build from an integration gets `429` on all requests until traffic falls back under the limit. Body and `Retry-After` **not stated** | Never returns `429` | Retries with backoff, honouring `Retry-After` capped by `SIMPRO_MAX_RETRY_DELAY` (ADR-010, ADR-012); default 8 req/s per client instance | Unknown (body, `Retry-After`) |
| 11 | Server errors (`5xx`) | **Not stated** | Only on an unhandled exception | Retries `502`, `503`, `504` and raises `SimproServerError` otherwise | Unknown |
| 12 | Customer detail without its type (`/customers/{id}`) | **Stated** (Split routes): error body `{"error": "Invalid resource URI. ...", "_href": "..."}`; status not given | No such route, so FastAPI `404` `{"detail": "Not Found"}` | Never calls it; uses the typed `/customers/companies/` and `/customers/individuals/` routes | Cosmetic |

## 4. Authentication (found while reading the docs)

Not in W1 T2's list, but each one decides whether the first sandbox call
works, so they are recorded here.

| # | Point | Docs say | Mock | Client | Severity |
|---|---|---|---|---|---|
| 13 | Token request encoding | **Stated** (Client credentials grant workflow): "Post to the <Token URL> with the following json data" `{"grant_type": "client_credentials", "client_id": ..., "client_secret": ...}` | Reads form fields (`Form(...)` in `routers.py`, `issue_token`) and accepts any credentials | Sends `application/x-www-form-urlencoded` (`auth.py`, `_refresh_token`) | Unknown. The docs show JSON; OAuth2 (RFC 6749) specifies form encoding, and many servers accept both. If Simpro accepts only JSON, every client call fails at authentication. First thing to check on the sandbox |
| 14 | Access token lifetime | **Stated**: `expires_in: 3600`, `token_type: Bearer`, `scope` unused; no refresh token for client credentials | Static token, no expiry | Reads `expires_in` (default 3600) and refreshes 60 s early | Match |
| 15 | Fetching a new token invalidates the old one | **Stated**: "Before or after the token expires, repeat the above to fetch a new access token. The old token will no longer be usable." | Never invalidates | One token per `AuthManager`; ADR-012's lock serialises refreshes within one client instance only | Unknown. Two client instances sharing one set of credentials (for example `clive-gateway` and a sandbox test run) would keep invalidating each other's tokens. Per-instance or per-credential scope is not stated; check on the sandbox |
| 16 | Rate limit threshold | **Stated**: 10 requests per second per build (row 10) | — | 8 req/s per client instance (ADR-010); within the limit for the single-worker gateway | Match |

## 5. Count by severity

| Severity | Count | Items |
|---|---|---|
| Breaks client | **0** | — |
| Cosmetic | **4** | 3, 5, 8, 12 |
| Unknown | **9** | 1, 4, 6, 7, 9, 10, 11, 13, 15 |
| Match | **3** | 2, 14, 16 |

No difference is confirmed to break the client, so W1 T4 has nothing to fix
on current evidence. Four of the unknowns would break the client if they go
the wrong way: **13** (token encoding), **15** (token invalidation across
instances), **4** (`/companies/` headers) and **1** (`ID` in projections, only
for callers that omit it). They are the first checks for the sandbox contract
tests (W1 T3, run in W1 T5).

One of the four roadmap items is now settled: the `Result-*` headers exist and
are documented (item 2). The other three stay unverifiable without live access.
