"""Tests for authentication module."""

import time

import pytest
import respx
from httpx import Response

from simpro_client.auth import AuthManager
from simpro_client.config import SimproSettings
from simpro_client.exceptions import SimproAuthError


@respx.mock
def test_token_obtained_on_first_call(mock_settings: SimproSettings):
    respx.post(mock_settings.token_url).mock(
        return_value=Response(200, json={"access_token":
                                         "fresh_token",
                                           "expires_in": 3600})
    )
    auth = AuthManager(mock_settings)
    token = auth.get_token()
    assert token == "fresh_token"
    auth.close()

@respx.mock
def test_token_cached_on_second_call(mock_settings: SimproSettings):
    route = respx.post(mock_settings.token_url).mock(
        return_value=Response(200, json={"access_token": "cached-token", "expires_in": 3600})
    )
    auth = AuthManager(mock_settings)
    auth.get_token()
    auth.get_token()
    assert route.call_count == 1
    auth.close()


@respx.mock
def test_expired_token_triggers_refresh(mock_settings: SimproSettings):
    route = respx.post(mock_settings.token_url).mock(
        return_value=Response(200, json={"access_token": "refreshed-token", "expires_in": 3600})
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
    with pytest.raises(SimproAuthError, match="401"):
        auth.get_token()
    auth.close()


def test_api_key_mode_returns_static_token(api_key_settings: SimproSettings):
    auth = AuthManager(api_key_settings)
    token = auth.get_token()
    assert token == "test_static_token"
    auth.close()
