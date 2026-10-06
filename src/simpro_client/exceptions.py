"""Typed exception hierarchy for Simpro API errors."""


class SimproError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SimproAuthError(SimproError):
    """Obtaining an access token failed (ADR-011).

    ``status_code`` is the token endpoint's HTTP status, or ``None`` when no
    response was received or no request was made (e.g. a missing API key).
    ``method``, ``url`` and ``correlation_id`` describe the API request that
    needed the token; the client fills them in (ADR-010 §2.4).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        method: str | None = None,
        url: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.method = method
        self.url = url
        self.correlation_id = correlation_id


class SimproAPIError(SimproError):
    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str = "",
        *,
        method: str | None = None,
        url: str | None = None,
        correlation_id: str | None = None,
        retry_count: int = 0,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.method = method
        self.url = url
        self.correlation_id = correlation_id
        self.retry_count = retry_count


class SimproClientError(SimproAPIError):
    pass


class SimproRateLimitError(SimproClientError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        *,
        method: str | None = None,
        url: str | None = None,
        response_body: str = "",
        correlation_id: str | None = None,
        retry_count: int = 0,
        attempt_count: int = 1,
    ) -> None:
        self.retry_after = retry_after
        self.attempt_count = attempt_count
        super().__init__(
            message,
            429,
            response_body,
            method=method,
            url=url,
            correlation_id=correlation_id,
            retry_count=retry_count,
        )


class SimproNotFoundError(SimproClientError):
    def __init__(self, message: str = "Resource not found", **context) -> None:
        super().__init__(message, 404, **context)


class SimproAuthRefreshError(SimproClientError, SimproAuthError):
    """The token refresh after a 401 response failed (ADR-010 §2.2).

    It is both a ``SimproClientError`` (status 401, with request context) and
    a ``SimproAuthError``, so callers catching either parent still catch it.
    """

    def __init__(
        self, message: str = "Token refresh after 401 failed", **context
    ) -> None:
        super().__init__(message, 401, **context)


class SimproServerError(SimproAPIError):
    pass


class SimproProtocolError(SimproError):
    def __init__(
        self,
        message: str,
        *,
        method: str | None = None,
        url: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.method = method
        self.url = url
        self.correlation_id = correlation_id
        super().__init__(message)
