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


def test_customer_subtype_routes_are_type_scoped(token: str):
    """A subtype detail route 404s when the id names the other kind.

    The polymorphic ``/customers/`` list hands callers a ``Type`` and an
    ``_href``; following the wrong one must fail loudly rather than return a
    record of the wrong shape (ADR-013 decision 2).
    """
    headers = {"Authorization": f"Bearer {token}"}
    summaries = httpx.get(
        f"{BASE}/api/v1.0/companies/1/customers/", headers=headers
    ).json()

    by_type = {}
    for row in summaries:
        by_type.setdefault(row["Type"], row)
    assert set(by_type) == {"Individual", "Company"}, (
        f"the seed must provide both customer kinds, got {sorted(by_type)}"
    )

    # Each id resolves on its own subtype route...
    for kind, subtype in (("Individual", "individuals"), ("Company", "companies")):
        own = httpx.get(
            f"{BASE}/api/v1.0/companies/1/customers/{subtype}/{by_type[kind]['ID']}",
            headers=headers,
        )
        assert own.status_code == 200, f"{kind} should resolve under {subtype}"
        assert own.json()["Type"] == kind

    # ...and 404s on the other one.
    for kind, other in (("Individual", "companies"), ("Company", "individuals")):
        crossed = httpx.get(
            f"{BASE}/api/v1.0/companies/1/customers/{other}/{by_type[kind]['ID']}",
            headers=headers,
        )
        assert crossed.status_code == 404, (
            f"a {kind} id must not resolve under /{other}/, "
            f"got {crossed.status_code}"
        )


def test_customer_summary_href_points_at_a_fetchable_route(token: str):
    """Following a summary's ``_href`` returns that customer's full record.

    This is the only documented way to get from the list to the detail, since
    Simpro publishes no ``/customers/{id}``.
    """
    headers = {"Authorization": f"Bearer {token}"}
    summary = httpx.get(
        f"{BASE}/api/v1.0/companies/1/customers/?pageSize=1", headers=headers
    ).json()[0]

    detail = httpx.get(f"{BASE}{summary['_href']}", headers=headers)

    assert detail.status_code == 200, f"_href {summary['_href']} did not resolve"
    assert detail.json()["ID"] == summary["ID"]


def test_a_project_is_a_job_with_type_project(token: str):
    """Projects are jobs, not a resource of their own.

    Simpro publishes no Projects route; upstream a project is a job whose
    ``Type`` is ``"Project"`` (ADR-013 Wave C). So the mock must serve them
    through ``/jobs/`` and must not answer ``/projects/``.
    """
    headers = {"Authorization": f"Bearer {token}"}

    assert (
        httpx.get(f"{BASE}/api/v1.0/companies/1/projects/", headers=headers).status_code
        == 404
    ), "the mock still serves a Projects route"

    jobs = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=250", headers=headers
    ).json()
    assert jobs, "the mock seeded no jobs"

    types = set()
    for row in jobs:
        detail = httpx.get(
            f"{BASE}/api/v1.0/companies/1/jobs/{row['ID']}", headers=headers
        ).json()
        types.add(detail["Type"])
    assert "Project" in types, f"no Type=Project jobs are seeded, only {sorted(types)}"
    assert types <= {"Project", "Service", "Prepaid"}, f"undocumented Type in {types}"


def test_job_total_is_a_nested_object_with_two_decimal_money(token: str):
    """``Total`` is an object, and its members are exact to two places.

    The old mock returned a bare float. Both the narrow list projection and
    the detail route carry the three-way split (ADR-013).
    """
    headers = {"Authorization": f"Bearer {token}"}
    listed = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=1", headers=headers
    ).json()[0]

    assert set(listed) == {"ID", "Description", "Total"}, (
        f"the job list projection should be exactly ID, Description and Total, "
        f"got {sorted(listed)}"
    )
    assert set(listed["Total"]) == {"ExTax", "Tax", "IncTax"}

    for key, value in listed["Total"].items():
        assert isinstance(value, int | float), f"{key} is not a JSON number"
        assert round(float(value), 2) == float(value), (
            f"{key}={value} has more than two decimal places"
        )
