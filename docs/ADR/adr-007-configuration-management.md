# ADR-007: Configuration Management — pydantic-settings

## Status
Accepted (implemented, Phase 3)

## Context
`simpro_client` and `simpro_mock` each need environment-driven configuration (base URLs, credentials, company IDs, timeouts) that validates on startup, coexists safely in a shared root `.env` file with unrelated Postgres/PGVector settings, and integrates naturally with the Pydantic models already used elsewhere in the codebase.

## Decision
Use **pydantic-settings** for both packages:
- `simpro_client.config.SimproSettings` — env prefix `SIMPRO_`, `env_file=".env"`, `extra="ignore"`
- `simpro_mock.config.Settings` — env prefix `SIMPRO_MOCK_`

`extra="ignore"` is the key decision that lets both configs live in the same `.env` file as the Phase 2 `POSTGRES_*` variables without either raising validation errors on the other's keys.

## Alternatives Considered
- **Plain `os.environ` reads with manual validation** — rejected: no schema, no type coercion, no clear single source of truth for what configuration exists; error-prone as the number of settings grows.
- **`python-decouple` or bare `python-dotenv`** — rejected: `python-dotenv` is still used underneath (as a dependency), but without Pydantic's validation layer there's no fail-fast behavior on missing required fields (e.g. `client_id`), and no natural fit with the Pydantic response models already used in `simpro_mock`.

## Consequences
- Positive: missing required fields (e.g. `SIMPRO_CLIENT_ID`) fail fast and clearly at settings-construction time rather than surfacing as a confusing runtime error deep in a request.
- Positive: `get_settings()` is `lru_cache`d, so repeated calls don't re-parse the environment.
- Positive: prefix isolation (`SIMPRO_` vs `SIMPRO_MOCK_`) keeps client-side and mock-service-side configuration cleanly separated even though both currently live in the same `.env`.
- Neutral: `simpro_client` pins `pydantic-settings==2.14.2`; `simpro_mock` pins `2.15.0` — a minor version skew between the two packages that's currently harmless but worth aligning at some point.
