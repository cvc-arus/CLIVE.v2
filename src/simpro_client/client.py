"""Base HTTP client for the Simpro REST API."""

import logging
import random
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from simpro_client.auth import AuthManager
from simpro_client.config import SimproSettings, get_settings
from simpro_client.endpoints import (
    AssetsEndpoint,
    AttachmentsEndpoint,
    CompaniesEndpoint,
    ContactsEndpoint,
    CustomersEndpoint,
    EmployeesEndpoint,
    JobNotesEndpoint,
    JobsEndpoint,
    ProjectsEndpoint,
    QuotesEndpoint,
    SitesEndpoint,
    StatusesEndpoint,
)
from simpro_client.exceptions import (
    SimproAPIError,
    SimproClientError,
    SimproNotFoundError,
    SimproRateLimitError,
    SimproServerError,
)
from simpro_client.logging import RequestTimer, configure_logging, get_correlation_id
from simpro_client.rate_limiter import TokenBucket

_MAX_RETRY_DELAY_SECONDS = 60.0
# Transient failures are retried only for idempotent methods (ADR-010 §2.2).
_RETRYABLE_METHODS = frozenset({"GET"})
_TRANSIENT_STATUS_CODES = frozenset({502, 503, 504})
_TRANSIENT_TRANSPORT_ERRORS = (httpx.TimeoutException, httpx.NetworkError)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SimproClient:
    def __init__(self, settings: SimproSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._limiter = TokenBucket(
            self._settings.limiter_refill_rate, self._settings.limiter_capacity
        )
        self._auth = AuthManager(self._settings, limiter=self._limiter)
        self._logger = configure_logging()
        self._http = httpx.Client(
            base_url=self._settings.base_url,
            timeout=self._settings.timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        self._sleep = time.sleep
        self._random = random.random
        self._now = _utc_now
        self.companies = CompaniesEndpoint(self)
        self.customers = CustomersEndpoint(self)
        self.jobs = JobsEndpoint(self)
        self.quotes = QuotesEndpoint(self)
        self.contacts = ContactsEndpoint(self)
        self.sites = SitesEndpoint(self)
        self.assets = AssetsEndpoint(self)
        self.employees = EmployeesEndpoint(self)
        self.projects = ProjectsEndpoint(self)
        self.job_notes = JobNotesEndpoint(self)
        self.attachments = AttachmentsEndpoint(self)
        self.statuses = StatusesEndpoint(self)

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, json=None):
        return self._request("POST", path, json=json)

    def patch(self, path, json=None):
        return self._request("PATCH", path, json=json)

    def delete(self, path):
        return self._request("DELETE", path)

    def _get_response(self, path, params=None):
        return self._request_response("GET", path, params=params)

    def _request(self, method, path, params=None, json=None, _retry_on_401=True):
        response = self._request_response(
            method, path, params=params, json=json, _retry_on_401=_retry_on_401
        )
        return None if response.status_code == 204 else response.json()

    def _request_response(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        _retry_on_401: bool = True,
    ) -> httpx.Response:
        """Send one logical request through the shared resilience policy.

        Every attempt acquires from the rate limiter and carries the same
        correlation ID. A 401 refreshes the token once (separate budget).
        429 responses, and for GET also 502/503/504 responses and timeouts
        or network errors, share one retry budget of ``max_retries``.
        Other failures are mapped to the typed exceptions.
        """
        correlation_id = get_correlation_id()
        auth_retry_available = _retry_on_401
        rate_retry_count = 0
        attempt_count = 0
        retryable = method in _RETRYABLE_METHODS
        while True:
            token = self._auth.get_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Correlation-ID": correlation_id,
            }
            self._limiter.acquire()
            attempt_count += 1
            budget_left = rate_retry_count < self._settings.max_retries
            try:
                with RequestTimer() as timer:
                    response = self._http.request(
                        method=method,
                        url=path,
                        params=params,
                        json=json,
                        headers=headers,
                    )
            except httpx.HTTPError as exc:
                if (
                    retryable
                    and budget_left
                    and isinstance(exc, _TRANSIENT_TRANSPORT_ERRORS)
                ):
                    self._sleep(self._backoff_delay(rate_retry_count))
                    rate_retry_count += 1
                    continue
                raise SimproAPIError(
                    f"Request failed: {exc}",
                    0,
                    method=method,
                    url=path,
                    correlation_id=correlation_id,
                    retry_count=rate_retry_count,
                ) from exc
            self._log_request(method, path, response.status_code, timer.duration_ms)
            if response.status_code == 401 and auth_retry_available:
                self._auth.invalidate()
                auth_retry_available = False
                continue
            if response.status_code == 429:
                if not budget_left:
                    raise SimproRateLimitError(
                        retry_after=self._parse_retry_after(
                            response.headers.get("Retry-After")
                        ),
                        method=method,
                        url=path,
                        response_body=response.text,
                        correlation_id=correlation_id,
                        retry_count=rate_retry_count,
                        attempt_count=attempt_count,
                    )
                self._sleep(self._retry_delay(response, rate_retry_count))
                rate_retry_count += 1
                continue
            if (
                response.status_code in _TRANSIENT_STATUS_CODES
                and retryable
                and budget_left
            ):
                self._sleep(self._retry_delay(response, rate_retry_count))
                rate_retry_count += 1
                continue
            if response.status_code == 404:
                raise SimproNotFoundError(
                    f"Not found: {method} {path}", response_body=response.text,
                    method=method, url=path, correlation_id=correlation_id,
                )
            if 400 <= response.status_code < 500:
                raise SimproClientError(
                    f"Client error: {response.status_code} on {method} {path}",
                    response.status_code, response.text, method=method, url=path,
                    correlation_id=correlation_id, retry_count=rate_retry_count,
                )
            if response.status_code >= 500:
                raise SimproServerError(
                    f"Server error: {response.status_code} on {method} {path}",
                    response.status_code, response.text, method=method, url=path,
                    correlation_id=correlation_id, retry_count=rate_retry_count,
                )
            return response

    def _retry_delay(self, response: httpx.Response, retry_count: int) -> float:
        """Return the server's ``Retry-After`` delay, else the backoff delay."""
        retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
        if retry_after is not None:
            return retry_after
        return self._backoff_delay(retry_count)

    def _parse_retry_after(self, value):
        if value is None:
            return None
        candidate = value.strip()
        if candidate.isascii() and candidate.isdigit():
            return float(int(candidate))
        try:
            retry_at = parsedate_to_datetime(candidate)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            return None
        delay = (retry_at.astimezone(UTC) - self._now()).total_seconds()
        return delay if delay >= 0 else None

    def _backoff_delay(self, retry_count):
        return min(
            _MAX_RETRY_DELAY_SECONDS,
            (2**retry_count) * (0.5 + self._random()),
        )

    def _log_request(self, method, url, status_code, duration_ms):
        record = logging.LogRecord(
            "simpro_client", logging.INFO, "", 0,
            f"{method} {url} -> {status_code} ({duration_ms:.1f}ms)",
            None, None,
        )
        record.method = method
        record.url = url
        record.status_code = status_code
        record.duration_ms = round(duration_ms, 1)
        self._logger.handle(record)

    def close(self):
        self._http.close()
        self._auth.close()

    def __enter__(self):
        return self

    def __exit__(self, *args: Any):
        self.close()
