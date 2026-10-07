# Simpro Mock API Reference

Generated from `services/simpro_mock/simpro_mock/routers.py`, `schemas.py`, `models.py`, `filtering.py`, and `middleware.py`.

Base URL (Docker network): `http://simpro-mock:8000`
Base URL (host machine): `http://localhost:8100`

---

## 1. Authentication

### `POST /oauth2/token`

Simulates the Simpro OAuth2 Client Credentials grant. Accepts `application/x-www-form-urlencoded` body:

| Field | Required | Notes |
|---|---|---|
| `grant_type` | No (default `client_credentials`) | Not validated against a fixed set |
| `client_id` | No | Accepted but not checked against any real credential store |
| `client_secret` | No | Accepted but not checked |

**Response `200`:**
```json
{
  "access_token": "mock-access-token-simpro",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

The returned token value, and its `expires_in`, come from `simpro_mock`'s `Settings` (`SIMPRO_MOCK_MOCK_ACCESS_TOKEN`, `SIMPRO_MOCK_TOKEN_EXPIRES_IN`), not from a real credential exchange — any `client_id`/`client_secret` pair is accepted in this mock.

### Bearer requirement on all other routes

Every route except `/health`, `/oauth2/token`, `/docs`, `/openapi.json`, `/redoc` requires:
```
Authorization: Bearer <access_token>
```
- Missing or malformed header → `401 {"detail": "Missing Bearer token"}`
- Token that doesn't match the configured value → `401 {"detail": "Invalid access token"}`

## 2. Health Check

### `GET /health`
```json
{"status": "ok", "service": "simpro-mock", "version": "0.1.0"}
```
No auth required.

## 3. Pagination

All list endpoints accept:

| Param | Default | Constraint |
|---|---|---|
| `page` | 1 | `>= 1` |
| `pageSize` | 30 | `1–250` |

Response headers on every list endpoint:

| Header | Meaning |
|---|---|
| `Result-Total` | Total matching records across all pages |
| `Result-Count` | Records returned in this page |
| `Result-Pages` | Total number of pages |

## 4. Filtering

List endpoints accept arbitrary query params matching a known PascalCase field name. Supported fields: `ID`, `Name`, `CompanyID`, `GivenName`, `FamilyName`, `Email`, `Phone`, `Status`, `DateIssued`, `Total`, `CustomerID`. Unrecognized field names are silently ignored (not an error).

**Operators** — wrap the value in an operator function:

| Syntax | Meaning |
|---|---|
| `Field=value` | Exact match |
| `Field=gt(value)` | Greater than |
| `Field=lt(value)` | Less than |
| `Field=ge(value)` | Greater than or equal |
| `Field=le(value)` | Less than or equal |
| `Field=ne(value)` | Not equal |
| `Field=between(a,b)` | Inclusive range |
| `Field=in(a,b,c)` | Value in set |
| `Field=!in(a,b,c)` | Value not in set |

Numeric operators (`gt`, `lt`, `ge`, `le`, `between`) attempt `int` then `float` casting; non-numeric values pass through as strings.

**Combining filters:** `search=all` (default) ANDs every filter together; `search=any` ORs them.

`page`, `pageSize`, `columns`, `orderby`, `search`, and `limit` are reserved and never treated as filter fields.

## 5. Resources

For every resource below: all fields are returned in PascalCase; `ID` is always the primary key; nested resources are scoped under `/api/v1.0/companies/{company_id}/...`.

**Routes** match Simpro's published spec, vendored at `docs/contracts/simpro-openapi-v1-get-subset.json` (ADR-013). **Field sets match for Wave A only** — Companies, Employees, Job Notes, Attachments and Project Status Codes. The rest are still the mock's original invented shapes and are re-shaped in Waves B and C. `tests/test_spec_conformance.py` reports which resources still differ.

Wave A resources return a **narrow projection from the collection route** and the full record from the detail route, as real Simpro does. Both field sets are listed below.

### Companies
- `GET /api/v1.0/companies/` — list, filterable/paginated
- `GET /api/v1.0/companies/{company_id}` — detail, `404` if not found

List fields: `ID`, `Name`

Detail fields: `ID`, `Name`, `Address` (`{Line1, Line2}`), `BillingAddress` (`{Line1, Line2}`), `Phone`, `Fax`, `Email`, `Website`, `Country`, `Currency`, `Timezone`, `TimezoneOffset`, `CompanyNo`, `EIN`, `EmployerTaxRefNo`, `CISCertNo`, `Licence`, `TaxName`, `DefaultLanguage`, `DefaultCostCenter` (always `null`), `SingleCostCenterMode`, `SimproPayments`, `Template`, `MultiCompanyLabel`, `MultiCompanyColor`, `ScheduleFormat`, `UIDateFormat`, `UITimeFormat`, `DateModified`

`Banking` is documented upstream but out of ADR-013's fidelity scope.

### Customers
- `GET /api/v1.0/companies/{company_id}/customers/`
- `GET /api/v1.0/companies/{company_id}/customers/{customer_id}`

Fields: `ID`, `CompanyID`, `GivenName`, `FamilyName`, `Email` (nullable), `Phone` (nullable)

### Jobs
- `GET /api/v1.0/companies/{company_id}/jobs/`
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}`

Fields: `ID`, `CompanyID`, `Name`, `Status`, `DateIssued` (nullable ISO date), `Total`

### Quotes
- `GET /api/v1.0/companies/{company_id}/quotes/`
- `GET /api/v1.0/companies/{company_id}/quotes/{quote_id}`

Fields: `ID`, `CompanyID`, `CustomerID` (nullable), `Name`, `Status`, `Total`

### Contacts
- `GET /api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/`
- `GET /api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}`

Fields: `ID`, `CompanyID`, `CustomerID`, `GivenName`, `FamilyName`, `Position` (nullable), `Email` (nullable), `Phone` (nullable)

### Sites
- `GET /api/v1.0/companies/{company_id}/sites/`
- `GET /api/v1.0/companies/{company_id}/sites/{site_id}`

Fields: `ID`, `CompanyID`, `CustomerID`, `Name`, `Address`, `City`, `Postcode`, `State`, `Country` (all address fields nullable)

### Assets
- `GET /api/v1.0/companies/{company_id}/sites/{site_id}/assets/`
- `GET /api/v1.0/companies/{company_id}/sites/{site_id}/assets/{asset_id}`

Fields: `ID`, `CompanyID`, `SiteID`, `AssetNo`, `Name`, `SerialNo` (nullable), `Model` (nullable), `Manufacturer` (nullable), `InstalledDate` (nullable ISO date)

### Employees
- `GET /api/v1.0/companies/{company_id}/employees/`
- `GET /api/v1.0/companies/{company_id}/employees/{employee_id}`

List fields: `ID`, `Name`

Detail fields: `ID`, `Name`, `Position`, `PrimaryContact` (`{Email, SecondaryEmail, WorkPhone, CellPhone, Extension, Fax, PreferredNotificationMethod}`), `Address` (`{Address, City, State, PostalCode, Country}`), `Zones` (array of `{ID, Name}`), `DefaultZone`, `DefaultCompany`, `Archived`, `DateCreated`, `DateModified`

There is no `CompanyID` — the company is in the path. An employee has a single `Name`, not `GivenName`/`FamilyName`. `Banking` and `PayRates` are out of ADR-013's fidelity scope.

### Job Notes
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/notes/`
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/notes/{note_id}`

List fields: `ID`, `Subject` (nullable), `Reference` (`{Text, Number, Type}`), `Visibility` (`{Admin, Customer}`)

Detail fields: the above plus `Note` (nullable), `DateCreated`, `FollowUpDate` (nullable ISO date), `Attachments` (always `[]`), `SubmittedBy` (nullable `{ID, Name, Type, TypeId}`), `AssignTo` (same shape, nullable)

There is no `JobID` — the job is in the path.

### Attachments
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/files/`
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/files/{file_id}`

List fields: `ID`, `Filename`

Detail fields: `ID`, `Filename`, `MimeType`, `FileSizeBytes`, `DateAdded`, `Public`, `Email` (boolean — whether the file rides along on outgoing email), `Folder` (always `null`), `AddedBy` (nullable `{ID, Name, Type, TypeId}`)

**`ID` is a string**, not an integer (`file-0001` in the seed). There is no `JobID` — the job is in the path.

### Project Status Codes
- `GET /api/v1.0/companies/{company_id}/setup/statusCodes/projects/`
- `GET /api/v1.0/companies/{company_id}/setup/statusCodes/projects/{status_code_id}`

Job and quote statuses draw their IDs from this list: the spec documents the `Status` field of the Job POST, Job PATCH and Quote POST bodies as "ID of a project status code".

List fields: `ID`, `Name`

Detail fields: `ID`, `Name`, `Color` (nullable hex), `Priority`, `DateModified`

There is no `CompanyID`, `Category` or `IsDefault` — none of the three exists upstream.

## 6. Seed Data

Two companies are seeded on container start (`simpro_mock/seed.py`, run via the Dockerfile's `CMD` before `uvicorn` starts):

| Company | ID | Approx. seeded volume |
|---|---|---|
| CVC Service | 1 | 8 customers, 8 jobs, 3 zones, plus proportional sites/contacts/assets/projects/notes/statuses |
| CVC Projects | 2 | 8 customers, 8 jobs, 3 zones, plus proportional sites/contacts/assets/projects/notes/statuses |

Attachments are not seeded per company: `seed.py` adds 1–3 attachments to each of the first 10 jobs returned by its job query (`jobs[:10]`).

`truncate_tables()` runs first and resets identity sequences, so re-running the seed script is idempotent (safe to run repeatedly).

## 7. Known Limitations (by design — see ADR)

- No real credential validation on `/oauth2/token` (any client_id/secret accepted)
- No rate limiting — the mock never returns `429`, unlike real Simpro's documented 10 req/sec/build limit
- No webhooks / async event callbacks
- No Projects resource — correct, since Simpro has none (a project is a Job with `Type: "Project"`). The `projects` table is still seeded but unreachable; it becomes `Type="Project"` jobs in ADR-013's Wave C
- `columns` is accepted and ignored. `simpro_client` sends it, but the mock cannot yet narrow a response to the requested fields (ADR-013 S6). Wave A resources do return Simpro's narrow default projection from their collection routes; resources awaiting their wave return every modelled field on both legs
- Thin data behind correct shapes in Wave A: `Attachment.Folder` and `Company.DefaultCostCenter` are always `null`, `JobNote.Attachments` is always `[]`, and `Employee.Zones` holds only that employee's default zone
- Read-only: no POST/PATCH/DELETE routes, no business-logic state transitions (e.g. Quote → Job conversion)
