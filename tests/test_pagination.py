
import pytest
from httpx import Response
from pydantic import BaseModel

from simpro_client.client import SimproClient
from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.exceptions import SimproProtocolError


# 1. Define a Mock Model
class MockModel(BaseModel):
    id: int
    name: str

# 2. Correctly declare MockEndpoint class-level fields to match ResourceEndpoint
class MockEndpoint(ResourceEndpoint[MockModel]):
    model = MockModel
    collection_path = "/companies/{company_id}/mock-resources/"
    detail_path = "/companies/{company_id}/mock-resources/{mock_resource_id}/"
    item_key = "mock_resource_id"


@pytest.fixture
def client(mock_settings) -> SimproClient:
    """Fixture to initialize our client using the shared mock_settings fixture."""
    return SimproClient(mock_settings)


@pytest.fixture(autouse=True)
def mock_oauth_token(respx_mock, client):
    """
    Automatically mocks the OAuth token POST request for all tests in this file.
    This satisfies the client's auth layer and returns a dummy access token.
    """
    respx_mock.post(client._settings.token_url).mock(
        return_value=Response(
            200,
            json={
                "access_token": "mock-access-token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        )
    )


def test_pagination_lazy_evaluation(respx_mock, client: SimproClient):
    """
    Verifies that iter_all() is truly lazy. 
    No HTTP requests should be dispatched when creating the generator.
    """
    base_url = client._settings.base_url
    route = respx_mock.get(f"{base_url}/companies/123/mock-resources/")
    route.mock(return_value=Response(
        200,
        json=[{"id": 1, "name": "Item 1"}],
        headers={"Result-Pages": "1"}
    ))

    # Instantiate MockEndpoint with only the client
    endpoint = MockEndpoint(client)

    # Call the generator method. This should NOT trigger a request.
    iterator = endpoint.iter_all(company_id=123)

    assert route.call_count == 0

    # Trigger evaluation by pulling the first element
    first_item = next(iterator)

    assert route.call_count == 1
    assert first_item.id == 1
    assert first_item.name == "Item 1"


def test_pagination_multi_page_success(respx_mock, client: SimproClient):
    """
    Verifies that the iterator cleanly fetches all pages sequentially,
    parses each element into the target Pydantic model, and terminates correctly.
    """
    base_url = client._settings.base_url
    p1_route = respx_mock.get(f"{base_url}/companies/123/mock-resources/").mock(
        side_effect=[
            Response(
                200,
                json=[{"id": 1, "name": "Item A"}],
                headers={"Result-Pages": "2"}
            ),
            Response(
                200,
                json=[{"id": 2, "name": "Item B"}],
                headers={"Result-Pages": "2"}
            )
        ]
    )

    endpoint = MockEndpoint(client)

    results = list(endpoint.iter_all(company_id=123, page_size=1))

    assert len(results) == 2
    assert all(isinstance(item, MockModel) for item in results)
    assert results[0].name == "Item A"
    assert results[1].name == "Item B"
    assert p1_route.call_count == 2


@pytest.mark.parametrize(
    "bad_headers, description",
    [
        ({}, "Missing Result-Pages header entirely"),
        ({"Result-Pages": "not-an-int"}, "Malformed, non-integer page counts"),
        ({"Result-Pages": "0"}, "Invalid edge-case page count (0)"),
    ],
)
def test_pagination_protocol_error_on_bad_metadata(respx_mock, client: SimproClient, bad_headers: dict, description: str):
    """
    Verifies that the client raises a SimproProtocolError when the server returns 
    missing or malformed pagination headers.
    """
    base_url = client._settings.base_url
    respx_mock.get(f"{base_url}/companies/123/mock-resources/").mock(
        return_value=Response(200, json=[{"id": 1, "name": "Test"}], headers=bad_headers)
    )

    endpoint = MockEndpoint(client)
    iterator = endpoint.iter_all(company_id=123)

    with pytest.raises(SimproProtocolError) as exc_info:
        next(iterator)

    assert "Result-Pages" in str(exc_info.value) or "pagination" in str(exc_info.value).lower()
