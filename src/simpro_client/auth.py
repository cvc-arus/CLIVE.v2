"""OAuth2 Client Credentials authentication manager."""

import time
from typing import Any

import httpx

from simpro_client.config import SimproSettings
from simpro_client.exceptions import SimproAuthError


class AuthManager:
    """Manages OAuth2 token lifecycle.

    Supports two modes:
    - client_credentials: Obtains tokens from the OAuth2 token endpoint
    - api_key: Uses a static Bearer token from configuration
    """

    def __init__(self, settings: SimproSettings) -> None:
        self._settings = settings
        self._access_token: str | None = None
        self._token_expiry: float = 0.0
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
        """Return a cached token or fetch a new one."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
        return self._refresh_token()

    def _refresh_token(self) -> str:
        """Fetch a new token from the OAuth2 endpoint."""
        payload: dict[str, Any] = {
            "grant_type": "client_credentials",
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
        }
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
                f"Token endpoint returned {response.status_code}: {response.text}"
            )

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = time.time() + expires_in - 60
        return self._access_token

    def invalidate(self) -> None:
        """Force token refresh on next call."""
        self._access_token = None
        self._token_expiry = 0.0

    def close(self) -> None:
        """Close the internal HTTP client."""
        self._http_client.close()
