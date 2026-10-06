# Configuration management using pyantic-settings.
# This module defines the configuration settings for the SimPro client application.
# It uses Pydantic's BaseSettings to load and validate environment variables,
# ensuring that the application has access to the necessary configuration parameters."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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
        description="Base URL of the Simpro API (e.g. http://localhost:8100/api/v1.0)"
    )
    token_url: str = Field(description="OAuth2 token endpoint URL")
    client_id: str | None = Field(
        default=None,
        description="OAuth2 Client ID (required when auth_mode='client_credentials')",
    )
    client_secret: str | None = Field(
        default=None,
        description=(
            "OAuth2 Client Secret (required when auth_mode='client_credentials')"
        ),
    )
    api_key: str | None = Field(
        default=None,
        description="Static API key (required when auth_mode='api_key')",
    )
    auth_mode: Literal["client_credentials", "api_key"] = Field(
        default="client_credentials",
        description="Auth mode: 'client_credentials' or 'api_key'",
    )
    company_id_service: int = Field(
        default=1,
        description=(
            "Company ID for CVC Service. Reserved: nothing reads this. "
            "Endpoints take an explicit company_id argument."
        ),
    )
    company_id_projects: int = Field(
        default=2,
        description=(
            "Company ID for CVC Projects. Reserved: nothing reads this. "
            "Endpoints take an explicit company_id argument."
        ),
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries on transient failures",
    )
    limiter_capacity: int = Field(default=8)
    limiter_refill_rate: float = Field(default=8.0)

    @model_validator(mode="after")
    def _check_auth_mode_fields(self) -> "SimproSettings":
        """Require the credentials the selected ``auth_mode`` actually uses.

        ``client_credentials`` needs ``client_id`` and ``client_secret``;
        ``api_key`` needs ``api_key``. Fields the mode does not use may be
        left unset. An empty value counts as unset.
        """
        required = (
            ("client_id", "client_secret")
            if self.auth_mode == "client_credentials"
            else ("api_key",)
        )
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError(
                f"auth_mode={self.auth_mode!r} requires: {', '.join(missing)}"
            )
        return self


@lru_cache
def get_settings() -> SimproSettings:
    """Get cached application settings."""
    return SimproSettings()
