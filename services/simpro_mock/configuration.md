# Simpro Mock Service Configuration Reference

This document maps and specifies the environment configuration properties used by the mock Simpro REST API service (`simpro_mock`).

The application leverages Pydantic Settings to automatically resolve configuration fields from environment variables. All keys are prefixed with the root-level identifier `SIMPRO_MOCK_`.

---

## Environment Variables Directory

### 1. `SIMPRO_MOCK_DATABASE_URL`
* **Type**: `string`
* **Default Value**: `"postgresql://<db-user>:<db-password>@simpro-mock-db:5432/simpro_mock"`
* **Description**: The connection string pointing the FastAPI service to its backing PostgreSQL database. When deploying via Docker Compose, the database server is resolved using the internal DNS hostname `simpro-mock-db`.

### 2. `SIMPRO_MOCK_MOCK_CLIENT_ID`
* **Type**: `string`
* **Default Value**: `"mock-client-id"`
* **Description**: **Unused.** Defined in `config.py` but never read: the `/oauth2/token` route (`issue_token` in `routers.py`) accepts any client ID. See `docs/known-issues.md`.

### 3. `SIMPRO_MOCK_MOCK_CLIENT_SECRET`
* **Type**: `string`
* **Default Value**: `"mock-client-secret"`
* **Description**: **Unused.** Defined in `config.py` but never read: the `/oauth2/token` route (`issue_token` in `routers.py`) accepts any client secret. See `docs/known-issues.md`.

### 4. `SIMPRO_MOCK_MOCK_ACCESS_TOKEN`
* **Type**: `string`
* **Default Value**: `"mock-access-token-simpro"`
* **Description**: The static, persistent token issued by the `/oauth2/token` route. The custom system middleware (`BearerAuthMiddleware`) intercepts requests on secure resource paths and verifies them against this exact value.

### 5. `SIMPRO_MOCK_TOKEN_EXPIRES_IN`
* **Type**: `integer`
* **Default Value**: `3600` (1 Hour)
* **Description**: Specifies the simulated validation lifetime of the generated token payload (expressed in seconds) returned within JSON authorization responses.

---

## Overriding Configurations Locally

To override these default settings, set them as real environment variables, or under the `simpro-mock` service's `environment:` in `docker-compose.yml`. `Settings` has no `env_file`, so a `.env` file is not read:

```env
SIMPRO_MOCK_DATABASE_URL=postgresql://<db-user>:<db-password>@localhost:5433/simpro_mock
SIMPRO_MOCK_MOCK_ACCESS_TOKEN=my-custom-debug-token
```