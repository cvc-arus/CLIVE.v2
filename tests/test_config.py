"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from simpro_client.config import SimproSettings


def test_settings_load_from_values():
    """Settings load correctly when all values are provided."""
    settings = SimproSettings(
        _env_file=None,  # Ignores local .env file
        base_url="http://localhost:8000/api/v1.0",
        token_url="http://localhost:8000/oauth2/token",
        client_id="my-id",
        client_secret="my-secret",
    )
    assert settings.base_url == "http://localhost:8000/api/v1.0"
    assert settings.client_id == "my-id"
    assert settings.timeout == 30.0
    assert settings.company_id_service == 1
    assert settings.company_id_projects == 2


def test_settings_missing_required_field():
    """Missing required fields raise a validation error."""
    with pytest.raises(ValidationError) as exc_info:
        SimproSettings(
            _env_file=None,  # Ignores local .env file
            base_url="http://localhost:8000/api/v1.0",
            token_url="http://localhost:8000/oauth2/token",
            client_id="my-id",
            # client_secret is missing
        )
    assert "client_secret" in str(exc_info.value)


def test_settings_defaults():
    """Default values are applied correctly."""
    settings = SimproSettings(
        _env_file=None,  # Ignores local .env file
        base_url="http://localhost:8000/api/v1.0",
        token_url="http://localhost:8000/oauth2/token",
        client_id="id",
        client_secret="secret",
    )
    assert settings.auth_mode == "client_credentials"
    assert settings.api_key is None
    assert settings.max_retries == 3


def test_settings_accepts_api_key_auth_mode():
    """'api_key' is a valid auth_mode."""
    settings = SimproSettings(
        _env_file=None,  # Ignores local .env file
        base_url="http://localhost:8000/api/v1.0",
        token_url="http://localhost:8000/oauth2/token",
        client_id="id",
        client_secret="secret",
        api_key="static-key",
        auth_mode="api_key",
    )
    assert settings.auth_mode == "api_key"


def test_settings_api_key_mode_needs_no_oauth_credentials():
    """api_key mode does not require client_id / client_secret."""
    settings = SimproSettings(
        _env_file=None,  # Ignores local .env file
        base_url="http://localhost:8000/api/v1.0",
        token_url="http://localhost:8000/oauth2/token",
        api_key="static-key",
        auth_mode="api_key",
    )
    assert settings.client_id is None
    assert settings.client_secret is None
    assert settings.api_key == "static-key"


def test_settings_api_key_mode_requires_api_key():
    """api_key mode without an api_key fails at construction, not at request time."""
    with pytest.raises(ValidationError) as exc_info:
        SimproSettings(
            _env_file=None,  # Ignores local .env file
            base_url="http://localhost:8000/api/v1.0",
            token_url="http://localhost:8000/oauth2/token",
            auth_mode="api_key",
        )
    assert "api_key" in str(exc_info.value)


@pytest.mark.parametrize("omitted", ["client_id", "client_secret"])
def test_settings_client_credentials_requires_oauth_fields(omitted):
    """client_credentials mode names whichever OAuth credential is absent."""
    values = {
        "base_url": "http://localhost:8000/api/v1.0",
        "token_url": "http://localhost:8000/oauth2/token",
        "client_id": "id",
        "client_secret": "secret",
    }
    del values[omitted]
    with pytest.raises(ValidationError) as exc_info:
        SimproSettings(_env_file=None, **values)  # _env_file ignores local .env
    assert omitted in str(exc_info.value)


def test_settings_treats_empty_credential_as_missing():
    """An empty credential is rejected, not sent to the token endpoint."""
    with pytest.raises(ValidationError) as exc_info:
        SimproSettings(
            _env_file=None,  # Ignores local .env file
            base_url="http://localhost:8000/api/v1.0",
            token_url="http://localhost:8000/oauth2/token",
            client_id="id",
            client_secret="",
        )
    assert "client_secret" in str(exc_info.value)


@pytest.mark.parametrize("bad_mode", ["apikey", "client-credentials", "oauth", ""])
def test_settings_rejects_unknown_auth_mode(bad_mode):
    """An unrecognised auth_mode fails validation instead of defaulting to OAuth."""
    with pytest.raises(ValidationError) as exc_info:
        SimproSettings(
            _env_file=None,  # Ignores local .env file
            base_url="http://localhost:8000/api/v1.0",
            token_url="http://localhost:8000/oauth2/token",
            client_id="id",
            client_secret="secret",
            auth_mode=bad_mode,
        )
    assert "auth_mode" in str(exc_info.value)
