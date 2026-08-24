# ADR : Mocking the Simpro REST API Service for Local Integration Testing

## Status
Accepted

## Context
Our team is actively building `simpro_client`, a type-safe, modular Python integration package designed to interact with the Simpro REST API (v1.0). In an ideal development environment, integration paths are continuously validated against a live testing sandbox. However, waiting for live Simpro sandbox API access and valid tenant credentials often introduces severe bottlenecks, stalling all development pipelines that depend on external resources. 

To unblock the development team, run automated integration tests, and ensure maximum codebase quality under local conditions, we required an immediate way to simulate Simpro's HTTP interface.

## Decision
We decided to build and maintain a containerized, lightweight mock Simpro REST API service using **FastAPI** and **PostgreSQL** (packaged as part of our Docker Compose stack). 

This allows developers to spin up the entire application stack locally on a Linux system with a single command (`docker compose up -d`), providing a reliable local endpoint (`http://localhost:8100`) that mimics the actual behavior, authentication requirements, and payload structures of the live Simpro service.

---

## Capabilities & Coverage (What the Mock Covers)

To provide high-fidelity simulation so that client code remains completely unchanged when transitioning to production, the mock service implements:

1. **OAuth2 Flow Emulation**:
   * Simulates the Client Credentials grant type at `/oauth2/token`.
   * Accepts standard form-encoded parameters (`application/x-www-form-urlencoded`) matching Simpro's specs.
   * Returns a simulated JSON payload containing a valid bearer `access_token` and lifetime.

2. **Bearer Token Authentication Middleware**:
   * Uses customized Starlette-based `BearerAuthMiddleware` to intercept and validate HTTP headers.
   * Restricts secure resource paths to valid requests containing `Authorization: Bearer mock-access-token-simpro`.
   * Exempts infrastructure endpoints (such as `/health` and `/oauth2/token`) to allow normal handshakes and health monitors.
   * Returns precise `401 Unauthorized` responses upon token discrepancies.

3. **Database-Backed Scoped Routes**:
   * Houses persistent tables for Companies, Customers, Jobs, and Quotes using PostgreSQL and SQLAlchemy.
   * Exposes eight standard database routes mapped to Simpro's scoped paths (e.g., `/api/v1.0/companies/{company_id}/customers/`).
   * Automatically initializes databases and injects realistic mock datasets during initial container provisioning.

4. **Response Field Casing Fidelity**:
   * Leverages customized Pydantic models to output JSON payloads using **PascalCase** fields (e.g., returning `GivenName`, `CompanyID`, `DateIssued`, and `Total`) instead of typical Python `snake_case`. This resolves severe deserialization errors during client parsing loops.

5. **Header-Driven Pagination**:
   * Reads and processes `page` and `pageSize` queries.
   * Calculates offsets and returns partitioned records.
   * Injects the standard Simpro pagination metadata headers (`Result-Total`, `Result-Count`, `Result-Pages`) into the HTTP response.

---

## Out of Scope & Limitations (What the Mock Does NOT Cover)

To keep the service lightweight and maintainable, several production-level elements have been intentionally omitted:

1. **Production Credential Validation**:
   * The `/oauth2/token` route does not check standard client credentials against a persistent store or identity provider. It accepts any `client_id` and `client_secret` during development to issue the static dev access token.

2. **API Rate Limiting**:
   * Simpro limits connection volumes under real workloads. The mock service does not enforce rate limits or simulate HTTP `429 Too Many Requests` status codes under highly concurrent execution paths.

3. **Webhook Callbacks & Event Triggers**:
   * Simpro uses webhooks to notify third-party clients of resource lifecycle changes (e.g., Quote created/updated). The mock operates purely as an intake request-response API and does not dispatch asynchronous webhook callbacks.

4. **Complex State Validation & Side-effects**:
   * The mock service focuses on data retrieval (GET routes). It does not validate nested business logic, status change state-machines, or secondary side-effects (e.g., converting a Quote to a Job automatically inside the database).

## Consequences
* **Immediate Progress**: The client SDK development team is entirely unblocked and has verified key packaging and import namespaces locally.
* **Hermetic Integration Checks**: Continuous integration pipelines can execute localized suite sweeps using standard tools (like `pytest` or `httpx` validation scripts) without relying on internet access or active Simpro services.
* **Development Safety**: Zero risk of polluting live sandboxes or production data streams during active structural refactoring.