from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    mock_client_id: str = "mock-client-id"
    mock_client_secret: str = "mock-client-secret"
    mock_access_token: str = "mock-access-token-simpro"
    token_expires_in: int = 3600

    model_config = {"env_prefix": "SIMPRO_MOCK_"}


settings = Settings()
