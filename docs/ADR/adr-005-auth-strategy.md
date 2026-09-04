# ADR-005: Auth Strategy — Client Credentials (Default) + API Key Fallback

## Status
Accepted (implemented, Phase 3 Sprint 1)

## Context
Simpro exposes two relevant OAuth2 flows for third-party integrations: the **Client Credentials Grant** (machine-to-machine, no user login) and the **Authorization Code Grant** ("Log in with Simpro," user-facing). `simpro_client` is a headless backend integration with no end user in the loop, but the project also anticipated a possible future user-facing portal.

## Decision
Implement **OAuth2 Client Credentials** as the default auth mode (`SIMPRO_AUTH_MODE=client_credentials`), with a **static API Key fallback mode** (`SIMPRO_AUTH_MODE=api_key`) for development scenarios where a full OAuth round-trip isn't needed. `AuthManager` (`simpro_client/auth.py`) implements both behind one interface (`get_token()`), with the OAuth path adding in-memory token caching, a 60-second early-refresh buffer, and 401-triggered forced refresh via `invalidate()`.

**Authorization Code Grant is explicitly deferred**, to be revisited only when a user-facing feature (envisioned no earlier than Phase 6, the AI Sales Agent, or a later customer-facing portal) actually needs per-user Simpro identity.

## Alternatives Considered
- **Authorization Code Grant now** — rejected: adds a "Log in with Simpro" browser redirect flow with no current use case; `simpro_client` has no end user, only backend jobs and future phases acting on the company's behalf.
- **API Key only, no OAuth support** — rejected: real Simpro's primary documented integration path is Client Credentials; building only around a fallback would leave the library unable to talk to production Simpro when access is enabled.

## Consequences
- Positive: matches Simpro's documented machine-to-machine pattern; no unnecessary user-interaction flow built for a use case that doesn't exist yet.
- Positive: the API Key fallback mode makes local development and testing (including against `simpro-mock`, which issues a static token regardless of credentials) trivial.
- Deferred work: if/when a user-facing Simpro-integrated feature is built, a new ADR should cover adding Authorization Code Grant support — it is not a drop-in extension of the current `AuthManager` design.
