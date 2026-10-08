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

List endpoints accept query params matching a filterable PascalCase field name. **The filterable set is per resource**, defined by `FILTER_MAPS` in `services/simpro_mock/simpro_mock/filtering.py`:

| Resource | Filterable fields |
|---|---|
| Companies | `ID`, `Name` |
| Customers | `ID`, `Type`, `CompanyName`, `GivenName`, `FamilyName`, `Email`, `Phone`, `CustomerType`, `Archived` |
| Contacts | `ID`, `GivenName`, `FamilyName`, `Email`, `Position`, `Department` |
| Sites | `ID`, `Name`, `Archived` |
| Assets | `ID`, `StartDate`, `DisplayOrder`, `Archived` |
| Employees | `ID`, `Name`, `Position`, `Archived` |
| Jobs | `ID`, `Name`, `Description`, `Type`, `Stage`, `OrderNo`, `RequestNo`, `DateIssued` |
| Quotes | `ID`, `Name`, `Description`, `Type`, `Stage`, `DateIssued`, `IsClosed` |
| Job Notes | `ID`, `Subject` |
| Attachments | `ID`, `Filename`, `MimeType`, `Public` |
| Project Status Codes | `ID`, `Name`, `Priority` |

**An unrecognised field name returns `400`**, with a body naming the parameter, the resource and the fields that would have worked. It used to be ignored, which meant a caller received unfiltered data believing it was filtered — a renamed field could pass every test while doing nothing.

Only **scalar columns** are filterable. A nested wire object such as `Job.Total` or `Job.Status` is composed from several columns and is not one, so filtering on it is a `400` rather than a silent no-op. Real Simpro supports some nested filters, so this is narrower than upstream rather than different.

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

`page`, `pageSize`, `columns`, `orderby`, `search`, and `limit` are reserved and never treated as filter fields. All six are honoured, except that `/companies/` has no `limit` upstream (see §7).

### `columns` projection

`columns` is a csv list and is accepted on **detail routes as well as collections**, matching the contract. It selects **top-level keys only**, and a selected key yields its whole nested block — `columns=Status` on a job returns the entire `{ID, Name, Color}` object.

- `ID` is always included, even when not requested. **Unverified against live Simpro**; re-check on first live access.
- Unknown column names are ignored rather than rejected, because a caller may legitimately ask for a field the contract documents but this mock does not serve (such as `Totals`). Unlike an ignored filter, a missing column is visible in the response.
- `?columns=` with an empty value behaves as if omitted.
- A projected response still carries `Result-Total`, `Result-Count` and `Result-Pages`.
- Callers using the typed client must keep every field their model marks required: `Job` requires `ID`, `Description` and `Total`, so `columns=Description` returns a body the model rejects.

### `orderby` and `limit`

`orderby` is a csv list of column names; prefixing one with `-` reverses it, so
`orderby=Stage,-ID` sorts by stage ascending then by id descending. The names
are the same wire names the filters use, and for the same reason: only scalar
columns are orderable, so `orderby=Total` on a job is a `400` naming the fields
that would have worked.

- Ordering a column the response does not contain is fine — the job list
  projection is only `ID`, `Description` and `Total`, but `orderby=Stage` works.
- **Every collection is ordered even without `orderby`**, by `ID`, and `ID` is
  the final tiebreak when `orderby` is given. Without it, `.offset().limit()`
  has no defined row order in PostgreSQL and page boundaries would not be
  stable.

`limit` narrows the page: the effective page size is the smaller of `pageSize`
and `limit`, `Result-Pages` is recomputed from it, and `Result-Total` still
reports the full filtered count. `limit=0` is a `422`.

**`limit`'s exact upstream semantics are unverified.** The contract says only
"Set the limit of number of records in a request"; "in a request" could instead
mean a cap on the whole result set across pages. Re-check on first live access.

## 5. Resources

For every resource below: all fields are returned in PascalCase; `ID` is always the primary key; nested resources are scoped under `/api/v1.0/companies/{company_id}/...`.

**Routes and field sets both match Simpro's published spec**, vendored at `docs/contracts/simpro-openapi-v1-get-subset.json` (ADR-013). Every check in `tests/test_spec_conformance.py` passes and its baseline file is empty, so every documented field name, type and optionality below is the vendor's, not the mock's.

Every resource returns a **narrow projection from the collection route** and the full record from the detail route, as real Simpro does. Both field sets are listed below.

### Companies
- `GET /api/v1.0/companies/` — list, filterable/paginated
- `GET /api/v1.0/companies/{company_id}` — detail, `404` if not found

List fields: `ID`, `Name`

Detail fields: `ID`, `Name`, `Address` (`{Line1, Line2}`), `BillingAddress` (`{Line1, Line2}`), `Phone`, `Fax`, `Email`, `Website`, `Country`, `Currency`, `Timezone`, `TimezoneOffset`, `CompanyNo`, `EIN`, `EmployerTaxRefNo`, `CISCertNo`, `Licence`, `TaxName`, `DefaultLanguage`, `DefaultCostCenter` (always `null`), `SingleCostCenterMode`, `SimproPayments`, `Template`, `MultiCompanyLabel`, `MultiCompanyColor`, `ScheduleFormat`, `UIDateFormat`, `UITimeFormat`, `DateModified`

`Banking` is documented upstream but out of ADR-013's fidelity scope.

### Customers

Customers are **polymorphic**: a customer is either an individual or a company, and the two have different name fields and different detail routes. There are three routes, and **no `/customers/{customer_id}`**.

- `GET /api/v1.0/companies/{company_id}/customers/` — both kinds, with the `Type` discriminator and an `_href`
- `GET /api/v1.0/companies/{company_id}/customers/individuals/`
- `GET /api/v1.0/companies/{company_id}/customers/individuals/{customer_id}`
- `GET /api/v1.0/companies/{company_id}/customers/companies/`
- `GET /api/v1.0/companies/{company_id}/customers/companies/{customer_id}`

Polymorphic list fields: `ID`, `Type` (`Individual`|`Company`), `CompanyName`, `GivenName`, `FamilyName`, `_href`

`_href` is the only documented way from the list to a full record. Following it is what the client does; each subtype detail route is **type-scoped** and returns `404` for an id of the other kind.

Individuals list: `ID`, `Type`, `GivenName`, `FamilyName`
Companies list: `ID`, `Type`, `CompanyName`

Shared detail fields: `ID`, `Type`, `Email`, `Phone`, `AltPhone`, `Address` (5-member object), `BillingAddress` (5-member object), `CustomerType`, `DoNotCall`, `Archived`, `AmountOwing` (JSON number, 2dp), `Profile` (`{Notes, Currency, AccountManager, CustomerGroup, CustomerProfile, ServiceJobCostCenter}`), `Sites`, `Tags` (always `[]`), `PreferredTechs` (always `[]`), `Contacts`, `Contracts` (always `null`), `ResponseTimes` (always `null`), `CustomFields` (always `[]`), `DateCreated`, `DateModified`

Individual detail adds: `GivenName`, `FamilyName`, `Title`, `CellPhone`
Company detail adds: `CompanyName`, `CompanyNumber`, `EIN`, `Fax`, `Website`

`Banking` and `Rates` are documented upstream but out of ADR-013's fidelity scope. There is no `CompanyID` — the company is in the path.

### Jobs
- `GET /api/v1.0/companies/{company_id}/jobs/`
- `GET /api/v1.0/companies/{company_id}/jobs/{job_id}`

A **project is a job with `Type: "Project"`** — Simpro has no Projects resource, and the mock's `projects` table is gone.

List fields: `ID`, `Description`, `Total`. That is the whole projection — not even `Name`.

`Total` is an **object**, `{ExTax, Tax, IncTax}`, each a JSON number exact to two decimal places (stored as `Numeric(12,2)`).

Detail fields: the above plus `Name`, `Type` (`Project`|`Service`|`Prepaid`), `Stage` (`Pending`|`Progress`|`Complete`|`Invoiced`|`Archived`), `Status` (`{ID, Name, Color}`), `Customer`, `Site`, `CustomerContract`, `CustomerContact` (null), `SiteContact` (null), `ProjectManager` (null), `Salesperson` (null), `Technician` (null), `Technicians` (`[]`), `AdditionalContacts` (`[]`), `Tags` (`[]`), `Notes`, `OrderNo`, `RequestNo`, `DateIssued`, `DueDate`, `CompletedDate`, `DateModified`, `AutoAdjustStatus`, `IsVariation`, `ConvertedFrom` (`{}`), `ArchiveReason` (null), `ResponseTime` (null), `CustomFields`

`Status.ID` is a **project status code id**: jobs, quotes and `/setup/statusCodes/projects/` share one id space, so `jobs.status_id` is a real foreign key. There is no `CompanyID`.

`Totals`, `ConvertedFromQuote` and `STC` are documented upstream but not served (see §7).

### Quotes
- `GET /api/v1.0/companies/{company_id}/quotes/`
- `GET /api/v1.0/companies/{company_id}/quotes/{quote_id}`

List fields: `ID`, `Description`, `Total` (the same object shape as a job's).

Detail fields: the above plus `Name`, `Type`, `Stage` (`InProgress`|`Complete`|`Approved` — different values from a job's), `CustomerStage` (null), `Status`, `Customer`, `Site`, `CustomerContract` (null), `CustomerContact` (null), `SiteContact` (null), `ProjectManager` (null), `Salesperson` (null), `Technician` (null), `Technicians` (`[]`), `AdditionalContacts` (`[]`), `AdditionalCustomers` (`[]`), `Tags` (`[]`), `Notes`, `OrderNo`, `RequestNo`, `JobNo` (null), `LinkedJobID` (null), `DateIssued`, `DateApproved`, `DueDate`, `DateModified`, `ValidityDays`, `AutoAdjustStatus`, `IsVariation`, `IsClosed`, `ArchiveReason` (null), `CustomFields`

There is no `CustomerID` — `Customer` is an object. `Totals` and `Forecast` are out of ADR-013's fidelity scope.

### Contacts
- `GET /api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/`
- `GET /api/v1.0/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}`

List fields: `ID`, `GivenName`, `FamilyName`

Detail fields: `ID`, `GivenName`, `FamilyName`, `Title`, `Position`, `Department`, `Email`, `WorkPhone`, `CellPhone`, `AltPhone`, `Fax`, `Notes`, the eight role flags (`JobContact`, `PrimaryJobContact`, `QuoteContact`, `PrimaryQuoteContact`, `InvoiceContact`, `PrimaryInvoiceContact`, `StatementContact`, `PrimaryStatementContact`), `Contact` (always `null`), `CustomFields` (always `[]`), `DateModified`

There is no `CompanyID` or `CustomerID`, and no single `Phone` — a contact has four numbers.

### Sites
- `GET /api/v1.0/companies/{company_id}/sites/`
- `GET /api/v1.0/companies/{company_id}/sites/{site_id}`

List fields: `ID`, `Name`

Detail fields: `ID`, `Name`, `Address` (5-member object), `BillingAddress` (4-member object — **no `Country`**, the one address shape upstream without it), `BillingContact`, `Customers` (array of customer refs), `PrimaryContact`, `PublicNotes`, `PrivateNotes`, `Zone`, `STCZone` (always `null`), `VEECZone` (always `null`), `PreferredTechs` (always `[]`), `PreferredTechnicians` (always `[]`), `CustomFields`, `Archived`, `DateModified`

A site belongs to **several** customers, through the `site_customers` table: `Site.Customers` and `Customer.Sites` are the same relation, which the old single `CustomerID` could not express. `Rates` is out of ADR-013's fidelity scope.

### Assets
- `GET /api/v1.0/companies/{company_id}/sites/{site_id}/assets/`
- `GET /api/v1.0/companies/{company_id}/sites/{site_id}/assets/{asset_id}`

List fields: `ID`, `AssetType` (`{ID, Name}`)

Detail fields: `ID`, `AssetType`, `StartDate`, `DisplayOrder`, `Archived`, `ParentID` (nullable), `LastTest` (`{Date, Result, ServiceLevel}`; `{}` for an untested asset), `CustomerContract` (nullable), `CustomFields`, `DateModified`

**There is no `AssetNo`, `Name`, `SerialNo`, `Model` or `Manufacturer`.** An asset is identified by its type, and the serial number, model and manufacturer live in `CustomFields` — which is where Simpro keeps them, and the reason custom fields are in ADR-013's fidelity scope at all. There is no `CompanyID` or `SiteID` either; both are in the path.

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
| CVC Service | 1 | 8 customers (4 individuals, 4 companies), 13 jobs (8 `Service` + 5 `Project`), 8 quotes, 3 zones, 8 asset types, plus proportional sites/contacts/assets/notes/statuses |
| CVC Projects | 2 | 8 customers (4 individuals, 4 companies), 13 jobs (8 `Service` + 5 `Project`), 8 quotes, 3 zones, 8 asset types, plus proportional sites/contacts/assets/notes/statuses |

Customers alternate between the two kinds within each company, so both subtype routes always return data. Custom fields are seeded for **sites** and **assets**; each asset carries Serial No, Model and Manufacturer there.

Attachments are not seeded per company: `seed.py` adds 1–3 attachments to each of the first 10 jobs returned by its job query (`jobs[:10]`).

`truncate_tables()` runs first and resets identity sequences, so re-running the seed script is idempotent (safe to run repeatedly).

## 7. Known Limitations (by design — see ADR)

- No real credential validation on `/oauth2/token` (any client_id/secret accepted)
- No rate limiting — the mock never returns `429`, unlike real Simpro's documented 10 req/sec/build limit
- No webhooks / async event callbacks
- No Projects resource — correct, since Simpro has none. A project is a job with `Type: "Project"`, and the `projects` table has been dropped; its rows are now `Type="Project"` jobs
- Not served, although documented upstream: the `Totals` block on jobs and quotes, `Forecast` on quotes, `Banking`/`Rates` on customers, `Rates` on sites, `Banking`/`PayRates` on employees — all out of ADR-013's fidelity scope. Also `Job.ConvertedFromQuote` and `STC`: the spec marks them required, but they are only meaningful for a converted job, and inventing values is the problem ADR-013 exists to fix. All are additive later and non-breaking, because the client models set `extra="ignore"`
- `limit` is honoured as a narrowing of `pageSize`, but the contract defines it only as "the limit of number of records in a request", so its exact semantics are **unverified** (see §4)
- The contract documents no `page`, `pageSize` or `limit` on `/companies/` — that collection is unpaginated upstream. The mock paginates it like every other collection; this predates ADR-013 and is left as is because the typed client pages it
- Thin data behind correct shapes in the re-shaped resources: `Attachment.Folder`, `Company.DefaultCostCenter`, `Customer.Contracts`, `Customer.ResponseTimes`, `Contact.Contact`, `Site.STCZone` and `Site.VEECZone` are always `null`; `JobNote.Attachments`, `Customer.Tags`, `Customer.PreferredTechs`, `Customer.CustomFields`, `Contact.CustomFields`, `Site.PreferredTechs` and `Site.PreferredTechnicians` are always `[]`; `Employee.Zones` holds only that employee's default zone
- Read-only: no POST/PATCH/DELETE routes, no business-logic state transitions (e.g. Quote → Job conversion)
