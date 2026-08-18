"""Typed exception hierarchy for Simpro API errors."""


class SimproError(Exception):
    """Base exception for all Simpro client errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SimproAuthError(SimproError):
    """Authentication or authorization failure."""

    pass


class SimproAPIError(SimproError):
    """API returned an error response."""

    def __init__(self, message: str, status_code: int, response_body: str = "") -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class SimproRateLimitError(SimproAPIError):
    """Rate limit exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message=message, status_code=429)


class SimproNotFoundError(SimproAPIError):
    """Resource not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)
