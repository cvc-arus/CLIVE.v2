"""Base HTTP client for the Simpro REST API."""

import logging
from typing import Any

import httpx

from simpro_client.auth import AuthManager
from simpro_client.config import SimproSettings, get_settings
from simpro_client.exceptions import (
    SimproAPIError,
    SimproNotFoundError,
    SimproRateLimitError,
)
from simpro_client.logging import (
    RequestTimer,
    configure_logging,
    get_correlation_id,
    set_correlation_id,
)


class SimproClient:
    """Main entry point for the Simpro API integration."""

    def __init__(self, settings: SimproSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._auth = AuthManager(self._settings)
        self._logger = configure_logging()
        # Configure httpx with base URL, timeout, and default headers
        self._http = httpx.Client(
            base_url=self._settings.base_url,
            timeout=self._settings.timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request."""
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Send a POST request."""
        return self._request("POST", path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Send a PATCH request."""
        return self._request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        """Send a DELETE request."""
        return self._request("DELETE", path)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        _retry_on_401: bool = True,
    ) -> Any:
        """Execute an HTTP request with auth, logging, and error handling."""
        cid = get_correlation_id() or set_correlation_id()
        token = self._auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        with RequestTimer() as timer:
            try:
                response = self._http.request(
                    method=method, url=path, params=params, json=json, headers=headers
                )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Request failed: {method} {path}: {e}",
                    extra={"method": method, "url": path},
                )
                raise SimproAPIError(
                    message=f"Request failed: {e}", status_code=0
                ) from e

        self._log_request(method, path, response.status_code, timer.duration_ms)
        return self._handle_response(
            response, method, path, params, json, _retry_on_401
        )

    def _handle_response(
        self,
        response: httpx.Response,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        retry_on_401: bool,
    ) -> Any:
        """Process the response, handling errors and retries."""
        if response.status_code == 401 and retry_on_401:
            self._logger.info("Received 401, refreshing token and retrying")
            self._auth.invalidate()
            return self._request(
                method, path, params=params, json=json, _retry_on_401=False
            )
        if response.status_code == 404:
            raise SimproNotFoundError(f"Not found: {method} {path}")
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise SimproRateLimitError(
                retry_after=float(retry_after) if retry_after else None
            )
        if response.status_code >= 400:
            raise SimproAPIError(
                message=f"API error: {response.status_code} on {method} {path}",
                status_code=response.status_code,
                response_body=response.text,
            )
        if response.status_code == 204:
            return None
        return response.json()

    def _log_request(
        self, method: str, url: str, status_code: int, duration_ms: float
    ) -> None:
        """Log request details with structured fields."""
        log_record = logging.LogRecord(
            name="simpro_client",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"{method} {url} -> {status_code} ({duration_ms:.1f}ms)",
            args=None,
            exc_info=None,
        )
        log_record.method = method
        log_record.url = url
        log_record.status_code = status_code
        log_record.duration_ms = round(duration_ms, 1)
        self._logger.handle(log_record)

    def close(self) -> None:
        """Close all underlying connections."""
        self._http.close()
        self._auth.close()

    def __enter__(self) -> "SimproClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
