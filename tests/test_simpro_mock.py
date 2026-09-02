"""Integration test: auth + query + response format."""

import httpx

BASE = "http://localhost:8100"

# Get a token from the mock OAuth2 endpoint
r = httpx.post(
    f"{BASE}/oauth2/token",
    data={
        "grant_type": "client_credentials",
        "client_id": "test",
        "client_secret": "test",
    },
)
assert r.status_code == 200, f"Token failed: {r.status_code}"
token = r.json()["access_token"]
print(f"Token: {token}")

# Query companies with Bearer auth
headers = {"Authorization": f"Bearer {token}"}
r = httpx.get(f"{BASE}/api/v1.0/companies/", headers=headers)
assert r.status_code == 200, f"Companies failed: {r.status_code}"
data = r.json()
assert "ID" in data[0], f"Expected PascalCase, got: {list(data[0].keys())}"
assert "Result-Total" in r.headers, "Missing Result-Total header"
print(f"Companies: {data}")
print(
    f"Headers: Total={r.headers['Result-Total']}, Count={r.headers['Result-Count']}, Pages={r.headers['Result-Pages']}"
)

# Verify 401 without auth
r = httpx.get(f"{BASE}/api/v1.0/companies/")
assert r.status_code == 401, f"Expected 401, got: {r.status_code}"
print(f"No-auth: {r.status_code} (expected 401)")

print("\nAll integration checks passed!")
