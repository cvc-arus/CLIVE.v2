from datetime import UTC, datetime

import respx
from httpx import Response

from simpro_client.client import SimproClient
from simpro_client.exceptions import (
    SimproClientError,
    SimproRateLimitError,
    SimproServerError,
)
from simpro_client.logging import set_correlation_id


class RecordingLimiter:
    def __init__(self):
        self.call_count = 0

    def acquire(self):
        self.call_count += 1


def token(settings):
    return respx.post(settings.token_url).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )


def capture(error_type, action):
    try:
        action()
    except error_type as exc:
        return exc
    raise AssertionError(f"{error_type.__name__} was not raised")


@respx.mock
def test_retry_after_forms_and_fallback(mock_settings):
    token(mock_settings)
    route = respx.get(f"{mock_settings.base_url}/jobs")
    delays = []
    route.mock(side_effect=[Response(429, headers={"Retry-After": "2"}), Response(200, json=[])])
    with SimproClient(mock_settings) as client:
        client._sleep = delays.append
        client.get("/jobs")
    assert delays == [2.0]

    route.mock(side_effect=[Response(429, headers={"Retry-After": "Thu, 01 Jan 2026 00:00:05 GMT"}), Response(200, json=[])])
    delays.clear()
    with SimproClient(mock_settings) as client:
        client._sleep = delays.append
        client._now = lambda: datetime(2026, 1, 1, tzinfo=UTC)
        client.get("/jobs")
    assert delays == [5.0]

    route.mock(side_effect=[Response(429, headers={"Retry-After": "1.5"}), Response(200, json=[])])
    delays.clear()
    with SimproClient(mock_settings) as client:
        client._sleep = delays.append
        client._random = lambda: 0.25
        client.get("/jobs")
    assert delays == [0.75]


@respx.mock
def test_401_then_429_keeps_independent_budgets(mock_settings):
    token_route = token(mock_settings)
    route = respx.get(f"{mock_settings.base_url}/jobs").mock(
        side_effect=[Response(401), Response(429, headers={"Retry-After": "1"}), Response(200, json=[])]
    )
    set_correlation_id("stable-retry-id")
    delays = []
    with SimproClient(mock_settings) as client:
        limiter = RecordingLimiter()
        client._limiter = limiter
        client._sleep = delays.append
        client.get("/jobs")
    assert token_route.call_count == 2
    assert limiter.call_count == 3
    assert delays == [1.0]
    assert [call.request.headers["X-Correlation-ID"] for call in route.calls] == ["stable-retry-id"] * 3


@respx.mock
def test_exhaustion_and_typed_errors(mock_settings):
    settings = mock_settings.model_copy(update={"max_retries": 2})
    token(settings)
    route = respx.get(f"{settings.base_url}/limited").mock(
        side_effect=[Response(429, text="slow", headers={"Retry-After": "1"})] * 3
    )
    with SimproClient(settings) as client:
        client._sleep = lambda seconds: None
        error = capture(SimproRateLimitError, lambda: client.get("/limited"))
    assert route.call_count == 3
    assert error.retry_count == 2
    assert error.attempt_count == 3

    respx.get(f"{settings.base_url}/bad").mock(return_value=Response(400, text="bad"))
    respx.get(f"{settings.base_url}/down").mock(return_value=Response(503, text="down"))
    with SimproClient(settings) as client:
        client_error = capture(SimproClientError, lambda: client.get("/bad"))
        server_error = capture(SimproServerError, lambda: client.get("/down"))
    assert client_error.status_code == 400
    assert server_error.status_code == 503
