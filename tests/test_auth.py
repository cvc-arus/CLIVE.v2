"""Tests for authentication module."""

import threading
import time

import httpx
import pytest
import respx
from httpx import Response

from simpro_client.auth import AuthManager
from simpro_client.config import SimproSettings
from simpro_client.exceptions import SimproAuthError


@respx.mock
def test_token_obtained_on_first_call(mock_settings: SimproSettings):
    respx.post(mock_settings.token_url).mock(
        return_value=Response(
            200, json={"access_token": "fresh_token", "expires_in": 3600}
        )
    )
    auth = AuthManager(mock_settings)
    token = auth.get_token()
    assert token == "fresh_token"
    auth.close()


@respx.mock
def test_token_cached_on_second_call(mock_settings: SimproSettings):
    route = respx.post(mock_settings.token_url).mock(
        return_value=Response(
            200, json={"access_token": "cached-token", "expires_in": 3600}
        )
    )
    auth = AuthManager(mock_settings)
    auth.get_token()
    auth.get_token()
    assert route.call_count == 1
    auth.close()


@respx.mock
def test_expired_token_triggers_refresh(mock_settings: SimproSettings):
    route = respx.post(mock_settings.token_url).mock(
        return_value=Response(
            200, json={"access_token": "refreshed-token", "expires_in": 3600}
        )
    )
    auth = AuthManager(mock_settings)
    auth.get_token()
    auth._token_expiry = time.time() - 1
    token = auth.get_token()
    assert token == "refreshed-token"
    assert route.call_count == 2
    auth.close()


@respx.mock
def test_invalid_credentials_raise_auth_error(mock_settings: SimproSettings):
    respx.post(mock_settings.token_url).mock(
        return_value=Response(401, text="Invalid client credentials")
    )
    auth = AuthManager(mock_settings)
    with pytest.raises(SimproAuthError, match="401") as exc_info:
        auth.get_token()
    assert exc_info.value.status_code == 401
    auth.close()


@respx.mock
def test_token_transport_error_has_no_status_code(mock_settings: SimproSettings):
    respx.post(mock_settings.token_url).mock(side_effect=httpx.ConnectError("down"))
    auth = AuthManager(mock_settings)
    with pytest.raises(SimproAuthError) as exc_info:
        auth.get_token()
    assert exc_info.value.status_code is None
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)
    auth.close()


def test_api_key_mode_returns_static_token(api_key_settings: SimproSettings):
    auth = AuthManager(api_key_settings)
    token = auth.get_token()
    assert token == "test_static_token"
    auth.close()


class CountingLimiter:
    def __init__(self):
        self.call_count = 0

    def acquire(self):
        self.call_count += 1


@respx.mock
def test_token_requests_acquire_from_limiter(mock_settings: SimproSettings):
    route = respx.post(mock_settings.token_url).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    limiter = CountingLimiter()
    auth = AuthManager(mock_settings, limiter=limiter)
    auth.get_token()
    auth.get_token()
    assert limiter.call_count == 1
    auth.invalidate()
    auth.get_token()
    assert limiter.call_count == 2
    assert route.call_count == 2
    auth.close()


def test_api_key_mode_does_not_acquire(api_key_settings: SimproSettings):
    limiter = CountingLimiter()
    auth = AuthManager(api_key_settings, limiter=limiter)
    auth.get_token()
    assert limiter.call_count == 0
    auth.close()


class _SerialisedTokenEndpoint:
    """Fake token endpoint that records how many threads are inside it.

    ``post()`` blocks on ``release`` instead of sleeping, so the test is
    deterministic and does not depend on wall-clock time.
    """

    def __init__(self, release: threading.Event) -> None:
        self.calls = 0
        self.max_concurrent = 0
        self.entered = threading.Event()
        self._inside = 0
        self._guard = threading.Lock()
        self._release = release

    def post(self, *args, **kwargs) -> Response:
        with self._guard:
            self.calls += 1
            self._inside += 1
            self.max_concurrent = max(self.max_concurrent, self._inside)
        self.entered.set()
        self._release.wait(timeout=5)
        with self._guard:
            self._inside -= 1
        return Response(200, json={"access_token": "tok", "expires_in": 3600})

    def close(self) -> None:
        """Match the httpx.Client interface AuthManager.close() expects."""


def test_concurrent_get_token_issues_one_request(mock_settings: SimproSettings):
    release = threading.Event()
    endpoint = _SerialisedTokenEndpoint(release)
    auth = AuthManager(mock_settings)
    auth._http_client = endpoint
    threads = [threading.Thread(target=auth.get_token) for _ in range(8)]
    for thread in threads:
        thread.start()
    assert endpoint.entered.wait(timeout=5), "no thread reached the token endpoint"
    release.set()
    for thread in threads:
        thread.join(timeout=5)
    assert not any(thread.is_alive() for thread in threads)
    assert endpoint.max_concurrent == 1
    assert endpoint.calls == 1
    auth.close()


@respx.mock
def test_invalidate_with_a_stale_token_keeps_the_cached_one(
    mock_settings: SimproSettings,
):
    route = respx.post(mock_settings.token_url).mock(
        side_effect=[
            Response(200, json={"access_token": "tok-1", "expires_in": 3600}),
            Response(200, json={"access_token": "tok-2", "expires_in": 3600}),
        ]
    )
    auth = AuthManager(mock_settings)
    assert auth.get_token() == "tok-1"
    auth.invalidate("a-stale-token-from-another-thread")
    assert auth.get_token() == "tok-1"
    assert route.call_count == 1
    auth.invalidate("tok-1")
    assert auth.get_token() == "tok-2"
    assert route.call_count == 2
    auth.close()


@respx.mock
def test_invalidate_without_a_token_always_clears(mock_settings: SimproSettings):
    route = respx.post(mock_settings.token_url).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )
    auth = AuthManager(mock_settings)
    auth.get_token()
    auth.invalidate()
    auth.get_token()
    assert route.call_count == 2
    auth.close()
