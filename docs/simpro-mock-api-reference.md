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

### Companies
- `GET /api/v1.0/companies/` — list, filterable/paginated
- `GET /api/v1.0/companies/{company_id}` — detail, `404` if not found

Fields: `ID`, `Name`

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

Fields: `ID`, `CompanyID`, `GivenName`, `FamilyName`, `Position` (nullable), `Email` (nullable), `Phone` (nullable)

### Projects
- `GET /api/v1.0/companies/{company_id}/projects/`
- `GET /api/v1.0/companies/{company_id}/projects/{project_id}`

Fields: `ID`, `CompanyID`, `CustomerID`, `SiteID` (nullable), `Name`, `Status`, `Total`

### Job Notes
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/notes/`
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/notes/{note_id}`

Fields: `ID`, `JobID`, `Subject` (nullable), `Note` (nullable), `CreatedBy` (nullable, employee id), `CreatedAt` (nullable ISO datetime)

### Attachments
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/`
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}/attachments/{attachment_id}`

Fields: `ID`, `JobID`, `Filename`, `MimeType` (nullable), `FileSize` (nullable, bytes), `UploadedAt` (nullable ISO datetime)

### Statuses
- `GET /api/v1.0/companies/{company_id}/statuses/`
- `GET /api/v1.0/companies/{company_id}/statuses/{status_id}`

Fields: `ID`, `CompanyID`, `Name`, `Category` (nullable, e.g. "Job"/"Quote"/"Project"), `IsDefault` (boolean)

## 6. Seed Data

Two companies are seeded on container start (`simpro_mock/seed.py`, run via the Dockerfile's `CMD` before `uvicorn` starts):

| Company | ID | Approx. seeded volume |
|---|---|---|
| CVC Service | 1 | 8 customers, 8 jobs, plus proportional sites/contacts/assets/projects/notes/attachments/statuses |
| CVC Projects | 2 | 8 customers, 8 jobs, plus proportional sites/contacts/assets/projects/notes/attachments/statuses |

`truncate_tables()` runs first and resets identity sequences, so re-running the seed script is idempotent (safe to run repeatedly).

## 7. Known Limitations (by design — see ADR)

- No real credential validation on `/oauth2/token` (any client_id/secret accepted)
- No rate limiting — the mock never returns `429`, unlike real Simpro's documented 10 req/sec/build limit
- No webhooks / async event callbacks
- Read-only: no POST/PATCH/DELETE routes, no business-logic state transitions (e.g. Quote → Job conversion)
