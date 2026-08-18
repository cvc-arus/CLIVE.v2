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
