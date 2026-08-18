# Configuration management using pyantic-settings.
# This module defines the configuration settings for the SimPro client application.
# It uses Pydantic's BaseSettings to load and validate environment variables,
# ensuring that the application has access to the necessary configuration parameters."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SimproSettings(BaseSettings):
    """Simpro API connection settings.

    All values are loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SIMPRO_",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: str = Field(
        description="Base URL of the Simpro API (e.g. http://simpro-mock:8000/api/v1.0)"
    )
    token_url: str = Field(description="OAuth2 token endpoint URL")
    client_id: str = Field(description="OAuth2 Client ID")
    client_secret: str = Field(description="OAuth2 Client Secret")
    api_key: str | None = Field(
        default=None,
        description="Static API key (fallback auth, optional)",
    )
    auth_mode: str = Field(
        default="client_credentials",
        description="Auth mode: 'client_credentials' or 'api_key'",
    )
    company_id_service: int = Field(
        default=1,
        description="Company ID for CVC Service",
    )
    company_id_projects: int = Field(
        default=2,
        description="Company ID for CVC Projects",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries on transient failures",
    )


@lru_cache
def get_settings() -> SimproSettings:
    """Get cached application settings."""
    return SimproSettings()
