"""Manual test: see structured logs in action."""

import respx
from httpx import Response

from simpro_client.client import SimproClient
from simpro_client.config import SimproSettings
from simpro_client.logging import set_correlation_id

# Set a known correlation ID for this operation
set_correlation_id("manual-test-001")

# Create test settings pointing at mocked endpoints
settings = SimproSettings(
    base_url="http://test.local/api/v1.0",
    token_url="http://test.local/oauth2/token",
    client_id="demo",
    client_secret="demo-secret",
)

# Mock the token endpoint and two API calls
with respx.mock:
    respx.post("http://test.local/oauth2/token").mock(
        return_value=Response(
            200, json={"access_token": "demo-tok", "expires_in": 3600}
        )
    )
    respx.get("http://test.local/api/v1.0/companies/1/jobs/").mock(
        return_value=Response(200, json=[{"ID": 1}])
    )
    respx.get("http://test.local/api/v1.0/companies/1/customers/").mock(
        return_value=Response(200, json=[{"ID": 42}])
    )

    with SimproClient(settings=settings) as client:
        client.get("/companies/1/jobs/")
        client.get("/companies/1/customers/")

print("\nCheck the JSON lines above for correlation_id: manual-test-001")