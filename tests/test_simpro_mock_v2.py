"""Live smoke tests against a running simpro-mock service."""

import httpx
import pytest

BASE = "http://localhost:8100"
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def require_mock() -> None:
    """Skip at test runtime, never while pytest imports or collects the module."""
    try:
        response = httpx.get(f"{BASE}/health", timeout=1.0)
        response.raise_for_status()
    except httpx.HTTPError:
        pytest.skip(
            "simpro-mock is not running on localhost:8100 "
            "(start it with: docker compose up -d simpro-mock)"
        )


@pytest.fixture(scope="module")
def token() -> str:
    response = httpx.post(
        f"{BASE}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "test",
            "client_secret": "test",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_companies_list_uses_pascal_case_and_pagination_headers(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{BASE}/api/v1.0/companies/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data
    assert "ID" in data[0]
    assert "Result-Total" in response.headers
    assert "Result-Pages" in response.headers
    assert "Result-Count" in response.headers


def test_unauthenticated_request_returns_401():
    response = httpx.get(f"{BASE}/api/v1.0/companies/")
    assert response.status_code == 401
