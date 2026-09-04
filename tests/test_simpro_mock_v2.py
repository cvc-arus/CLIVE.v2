"""Live smoke test against a running simpro-mock service.

Unlike a normal unit test, this exercises the real HTTP service (auth flow,
PascalCase field casing, pagination headers) end-to-end. It is skipped
automatically when the mock isn't reachable, so it no longer breaks
collection of the rest of the suite when nobody has run
``docker compose up -d simpro-mock`` first.
"""

import httpx
import pytest

BASE = "http://localhost:8100"


def _mock_is_running() -> bool:
    """Best-effort reachability check. Never raises."""
    try:
        httpx.get(f"{BASE}/health", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _mock_is_running(),
    reason=(
        "simpro-mock is not running on localhost:8100 "
        "(start it with: docker compose up -d simpro-mock)"
    ),
)


@pytest.fixture(scope="module")
def token() -> str:
    """Obtain a bearer token from the mock OAuth2 endpoint."""
    response = httpx.post(
        f"{BASE}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "test",
            "client_secret": "test",
        },
    )
    assert response.status_code == 200, f"Token request failed: {response.status_code}"
    return response.json()["access_token"]


def test_companies_list_uses_pascal_case_and_pagination_headers(token: str):
    """Companies list returns Simpro-shaped PascalCase JSON with headers."""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{BASE}/api/v1.0/companies/", headers=headers)

    assert response.status_code == 200, f"Companies request failed: {response.status_code}"
    data = response.json()
    assert data, "Expected at least one seeded company"
    assert "ID" in data[0], f"Expected PascalCase fields, got: {list(data[0].keys())}"
    assert "Result-Total" in response.headers, "Missing Result-Total header"
    assert "Result-Pages" in response.headers, "Missing Result-Pages header"
    assert "Result-Count" in response.headers, "Missing Result-Count header"


def test_unauthenticated_request_returns_401():
    """Requests without a Bearer token are rejected."""
    response = httpx.get(f"{BASE}/api/v1.0/companies/")
    assert response.status_code == 401, f"Expected 401, got: {response.status_code}"
