# Sprint 4 Implementation Contract: Typed Client Layer

This document forms the official implementation contract for Sprint 4. It provides the exact specifications, routes, and validation parameters required to construct the synchronous, type-safe Simpro client layer against the completed high-fidelity mock service.

---

## 1. General Contract Rules
All code written in Sprint 4 must comply with the following architectural rules:
*   **Mandatory Resources:** All twelve read-only resources must be fully implemented. No resource may be omitted.
*   **Case Translation:** The mock JSON payloads return PascalCase fields (aliases), but the public client must expose standard pythonic snake_case attributes.
*   **Unknown Field Tolerance:** All Pydantic models must silently discard extra unmapped API fields to prevent runtime parsing crashes.
*   **Type Safety:** Endpoint implementations must consume these validated Pydantic models rather than returning untyped dicts.

---

## 2. The 12-Resource Payload Matrix

| Resource Name | Committed List Route | Mock Field (Alias) | Python Attribute | Type & Optionality |
| :--- | :--- | :--- | :--- | :--- |
| **Company** | `/api/v1.0/companies/` | `ID``Name` | `id``name` | `int` (Required)`str` (Required) |
| **Customer** | `/api/v1.0/companies/{companyID}/customers/` | `ID``CompanyID``GivenName``FamilyName``Email``Phone` | `id``company_id``given_name``family_name``email``phone` | `int` (Required)`int` (Required)`str` (Required)`str` (Required)`str` (Optional)`str` (Optional) |
| **Job** | `/api/v1.0/companies/{companyID}/jobs/` | `ID``CompanyID``Name``Status``DateIssued``Total` | `id``company_id``name``status``date_issued``total` | `int` (Required)`int` (Required)`str` (Required)`str` (Required)`date` (Optional)`float` (Required) |
| **Quote** | `/api/v1.0/companies/{companyID}/quotes/` | `ID``CompanyID``CustomerID``Name``Status``Total` | `id``company_id``customer_id``name``status``total` | `int` (Required)`int` (Required)`int` (Optional)`str` (Required)`str` (Required)`float` (Required) |
| **Contact** | `/api/v1.0/companies/{companyID}/customers/{customerID}/contacts/` | `ID``CompanyID``CustomerID``GivenName``FamilyName``Position``Email``Phone` | `id``company_id``customer_id``given_name``family_name``position``email``phone` | `int` (Required)`int` (Required)`int` (Required)`str` (Required)`str` (Required)`str` (Optional)`str` (Optional)`str` (Optional) |
| **Site** | `/api/v1.0/companies/{companyID}/sites/` | `ID``CompanyID``CustomerID``Name``Address``City``Postcode``State``Country` | `id``company_id``customer_id``name``address``city``postcode``state``country` | `int` (Required)`int` (Required)`int` (Required)`str` (Required)`str` (Optional)`str` (Optional)`str` (Optional)`str` (Optional)`str` (Optional) |
| **Asset** | `/api/v1.0/companies/{companyID}/sites/{siteID}/assets/` | `ID``CompanyID``SiteID``AssetNo``Name``SerialNo``Model``Manufacturer``InstalledDate` | `id``company_id``site_id``asset_no``name``serial_no``model``manufacturer``installed_date` | `int` (Required)`int` (Required)`int` (Required)`str` (Required)`str` (Required)`str` (Optional)`str` (Optional)`str` (Optional)`date` (Optional) |
| **Employee** | `/api/v1.0/companies/{companyID}/employees/` | `ID``CompanyID``GivenName``FamilyName``Position``Email``Phone` | `id``company_id``given_name``family_name``position``email``phone` | `int` (Required)`int` (Required)`str` (Required)`str` (Required)`str` (Optional)`str` (Optional)`str` (Optional) |
| **Project** | `/api/v1.0/companies/{companyID}/projects/` | `ID``CompanyID``CustomerID``SiteID``Name``Status``Total` | `id``company_id``customer_id``site_id``name``status``total` | `int` (Required)`int` (Required)`int` (Required)`int` (Optional)`str` (Required)`str` (Required)`float` (Required) |
| **Job Note** | `/api/v1.0/companies/{companyID}/jobs/{jobID}/notes/` | `ID``JobID``Subject``Note``CreatedBy``CreatedAt` | `id``job_id``subject``note``created_by``created_at` | `int` (Required)`int` (Required)`str` (Optional)`str` (Optional)`str` (Optional)`datetime` (Optional) |
| **Attachment** | `/api/v1.0/companies/{companyID}/jobs/{jobID}/attachments/` | `ID``JobID``Filename``MimeType``FileSize``UploadedAt` | `id``job_id``filename``mime_type``file_size``uploaded_at` | `int` (Required)`int` (Required)`str` (Required)`str` (Optional)`int` (Optional)`datetime` (Optional) |
| **Status** | `/api/v1.0/companies/{companyID}/statuses/` | `ID``CompanyID``Name``Category``IsDefault` | `id``company_id``name``category``is_default` | `int` (Required)`int` (Required)`str` (Required)`str` (Optional)`bool` (Required) |

---

## 3. Model Package & Base Configuration

To prevent namespace clutter, each resource schema resides in its own module inside `src/simpro_client/models/`.

### Public Exports Surface
The export module `src/simpro_client/models/__init__.py` must act as the single export boundary:
```python
from simpro_client.models.company import Company
from simpro_client.models.customer import Customer
# ... export all 12 models ...
```

### Shared Configuration
The base class `src/simpro_client/models/base.py` enforces global Pydantic parameters:
```python
from pydantic import BaseModel, ConfigDict

class SimproBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        from_attributes=True
    )
```

---

## 4. Endpoints & Pagination Design

### Shared Endpoint Base (`src/simpro_client/endpoints/base.py`)
`ResourceEndpoint` centralizes request mapping, validation, and lazy listing:
*   **Compatibility Guard:** Endpoint operations call a private, response-preserving client request primitive. The public client methods (e.g. `client.get`) continue to return raw decoded JSON arrays, ensuring 100% backward compatibility with Sprint 1.
*   **Request Construction:** Accept explicit nested keys as function arguments (e.g., `company_id`, `site_id`) to map correctly to nested URLs.

### Lazy Iteration Protocol (`src/simpro_client/pagination.py`)
Our synchronous pagination contract enforces lazy fetching boundaries:
*   **Creation Phase:** Creating the iterator performs no HTTP request.
*   **Consumption Phase:** Grabbing the first element triggers the first page request.
*   **Page Retention:** The iterator retains only one page of records in memory.
*   **Boundary Execution:** Crossing a page boundary triggers exactly one subsequent request.
*   **Header Rules:** The total page count is read from the `Result-Pages` header. A missing or invalid header raises a typed `SimproProtocolError`.

---

## 5. Resilience & Error Handling Policy (ADR-005)

### Lock-Protected Token Bucket (`src/simpro_client/rate_limiter.py`)
Every outbound request must pass through a single rate limiter attached to the client instance:
*   **Configuration:** Lock-protected token bucket with a default rate of `8.0` requests per second.
*   **Concurrency Guard:** The lock is acquired to calculate tokens, but **must be released** before any sleep operation occurs to prevent block-locking other logical client threads.

### Bounded Retries & Authentication Recovery
*   **Retry Priority:** A 429 response first respects any numeric or date values inside the `Retry-After` header. If missing, it falls back to bounded exponential backoff with jitter up to the configured retry maximum.
*   **Correlation ID Propagation:** Every request attempt under a single invocation must propagate the same `X-Correlation-ID` header. Retries must never generate a new correlation ID.
*   **Error Hierarchy (`src/simpro_client/exceptions.py`):**
    *   `SimproError` (Base Exception)
        *   `SimproClientError` (For 4xx status codes, contains request context, correlation ID)
            *   `SimproRateLimitError` (For 429, contains Retry-After metadata)
        *   `SimproServerError` (For 5xx status codes)
        *   `SimproProtocolError` (For malformed pagination/data payloads)

---

## 6. Verification & Quality Gates

Before committing code, the developer must prove execution with the following offline/online validation suites.

### Gate 1: Static Quality Check
```bash
ruff check .
ruff format --check .
```

### Gate 2: Offline Unit Test Execution (Docker Stopped)
```bash
pytest -q -m "not integration"
```
*Tests must prove that Pydantic alias mapping, unknown field tolerance, and mock rate-limiting behavior run instantly and cleanly without hitting active servers.*

### Gate 3: Live Mock Integration Execution (Docker Running)
```bash
docker compose up -d --build simpro-mock
pytest -q -m integration
```
*Confirms model validation works against double-nested routes, multiple seeded company IDs, and validates that correlation IDs propagate completely through the live mock server middleware.*

---

## 7. Cleanup Path
To restore the developer sandbox while keeping the local database state intact:
```bash
docker compose down
```
*Note: Do not supply the `-v` flag to preserve database volume seed integrity.*
