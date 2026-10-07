"""OAuth2 Client Credentials authentication manager."""

import time
from threading import Lock
from typing import Any

import httpx

from simpro_client.config import SimproSettings
from simpro_client.exceptions import SimproAuthError
from simpro_client.rate_limiter import TokenBucket


class AuthManager:
    """Manages OAuth2 token lifecycle.

    Supports two modes:
    - client_credentials: Obtains tokens from the OAuth2 token endpoint
    - api_key: Uses a static Bearer token from configuration

    Refreshes are serialised by an internal lock, so concurrent callers
    produce one token request between them rather than one each
    (ADR-012 §2.2). The lock guards ``_access_token`` and
    ``_token_expiry``; ``api_key`` mode touches neither and is lock-free.
    """

    def __init__(
        self, settings: SimproSettings, limiter: TokenBucket | None = None
    ) -> None:
        """Create the manager.

        If ``limiter`` is given, every token request acquires from it first,
        so token traffic shares the client's rate budget (ADR-010 §2.1).
        """
        self._settings = settings
        self._limiter = limiter
        self._access_token: str | None = None
        self._token_expiry: float = 0.0
        self._lock = Lock()
        self._http_client = httpx.Client(timeout=settings.timeout)

    def get_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if self._settings.auth_mode == "api_key":
            return self._get_api_key_token()
        return self._get_oauth_token()

    def _get_api_key_token(self) -> str:
        """Return the static API key token."""
        if not self._settings.api_key:
            raise SimproAuthError("API key mode selected but no api_key configured")
        return self._settings.api_key

    def _get_oauth_token(self) -> str:
        """Return a cached token, fetching a new one at most once.

        The cache is read without the lock first, so the common hit costs
        nothing. On a miss the lock is taken and the cache re-read, because
        another thread may have refreshed while this one waited.
        """
        token = self._access_token
        if token and time.time() < self._token_expiry:
            return token
        with self._lock:
            token = self._access_token
            if token and time.time() < self._token_expiry:
                return token
            return self._refresh_token()

    def _refresh_token(self) -> str:
        """Fetch a new token from the OAuth2 endpoint.

        Called only with ``_lock`` held. It acquires the shared limiter
        while holding that lock; ``TokenBucket`` never calls back into this
        class, so the auth-then-bucket order cannot cycle (ADR-012 §4).
        """
        payload: dict[str, Any] = {
            "grant_type": "client_credentials",
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
        }
        if self._limiter is not None:
            self._limiter.acquire()
        try:
            response = self._http_client.post(
                self._settings.token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as e:
            raise SimproAuthError(f"Token request failed: {e}") from e

        if response.status_code != 200:
            raise SimproAuthError(
                f"Token endpoint returned {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = time.time() + expires_in - 60
        return self._access_token

    def invalidate(self, token: str | None = None) -> None:
        """Force a token refresh on the next call.

        Args:
            token: The token that was rejected. When given, the cache is
                cleared only if it still holds that token, so a late 401
                cannot discard a newer token another thread has just
                fetched (ADR-012 §2.2). When omitted, the cache is
                cleared unconditionally.
        """
        with self._lock:
            if token is not None and self._access_token != token:
                return
            self._access_token = None
            self._token_expiry = 0.0

    def close(self) -> None:
        """Close the internal HTTP client."""
        self._http_client.close()
