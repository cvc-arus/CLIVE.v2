"""Tests for the base HTTP client."""

import pytest
import respx
from httpx import Response

from simpro_client.client import SimproClient
from simpro_client.exceptions import (
    SimproNotFoundError,
    SimproRateLimitError,
)


@respx.mock
def test_successful_get(mock_settings):
    """Successful GET returns parsed JSON."""
    respx.post(mock_settings.token_url).mock(return_value=Response(200, json={"access_token": "tok", "expires_in": 3600}))
    respx.get(f"{mock_settings.base_url}/companies/1/jobs/").mock(return_value=Response(200, json=[{"ID": 1, "Name": "Test Job"}]))
    with SimproClient(settings=mock_settings) as client:
        data = client.get("/companies/1/jobs/")
    assert data == [{"ID": 1, "Name": "Test Job"}]


@respx.mock
def test_401_triggers_refresh_and_retry(mock_settings):
    """401 response triggers token refresh and retries the request."""
    token_route = respx.post(mock_settings.token_url).mock(return_value=Response(200, json={"access_token": "new-tok", "expires_in": 3600}))
    respx.get(f"{mock_settings.base_url}/companies/1/jobs/").mock(side_effect=[Response(401, text="Unauthorized"), Response(200, json=[{"ID": 1}])])
    with SimproClient(settings=mock_settings) as client:
        data = client.get("/companies/1/jobs/")
    assert data == [{"ID": 1}]
    assert token_route.call_count == 2


@respx.mock
def test_404_raises_not_found(mock_settings):
    """404 response raises SimproNotFoundError."""
    respx.post(mock_settings.token_url).mock(return_value=Response(200, json={"access_token": "tok", "expires_in": 3600}))
    respx.get(f"{mock_settings.base_url}/companies/1/jobs/999").mock(return_value=Response(404, text="Not Found"))
    with SimproClient(settings=mock_settings) as client:
        with pytest.raises(SimproNotFoundError):
            client.get("/companies/1/jobs/999")


@respx.mock
def test_429_raises_rate_limit_error(mock_settings):
    """429 response raises SimproRateLimitError with retry_after."""
    respx.post(mock_settings.token_url).mock(return_value=Response(200, json={"access_token": "tok", "expires_in": 3600}))
    respx.get(f"{mock_settings.base_url}/companies/1/jobs/").mock(return_value=Response(429, headers={"Retry-After": "5"}))
    with SimproClient(settings=mock_settings) as client:
        with pytest.raises(SimproRateLimitError) as exc_info:
            client.get("/companies/1/jobs/")
    assert exc_info.value.retry_after == 5.0


@respx.mock
def test_client_context_manager(mock_settings):
    """Client works as a context manager and closes cleanly."""
    respx.post(mock_settings.token_url).mock(return_value=Response(200, json={"access_token": "tok", "expires_in": 3600}))
    respx.get(f"{mock_settings.base_url}/companies/1/").mock(return_value=Response(200, json={"ID": 1, "Name": "CVC Service"}))
    with SimproClient(settings=mock_settings) as client:
        result = client.get("/companies/1/")
    assert result["Name"] == "CVC Service"
