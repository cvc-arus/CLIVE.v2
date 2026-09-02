"""Shared test fixtures for the tests."""

import pytest

from simpro_client.config import SimproSettings


@pytest.fixture
def mock_settings() -> SimproSettings:
    """create test settings without requiring .env file."""
    return SimproSettings(
        base_url="http://simpro-mock:8000/api/v1.0",
        token_url="http://simpro-mock:8000/oauth/token",
        client_id="mock_client_id",
        client_secret="mock_client_secret",
        # api_key="mock_api_key",
        auth_mode="client_credentials",
        company_id_service=1,
        company_id_projects=2,
        timeout=30.0,
        max_retries=3,
    )


@pytest.fixture
def api_key_settings() -> SimproSettings:
    """create test settings with API key auth mode."""
    return SimproSettings(
        base_url="http://simpro-mock:8000/api/v1.0",
        token_url="http://simpro-mock:8000/oauth/token",
        client_id="unused",
        client_secret="unused",
        api_key="test_static_token",
        auth_mode="api_key",
        company_id_service=1,
        company_id_projects=2,
        timeout=30.0,
        max_retries=3,
    )
