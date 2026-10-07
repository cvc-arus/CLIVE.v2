"""Offline tests for typed read-only endpoints."""

import pytest
import respx
from httpx import Response

from simpro_client import (
    Asset,
    Attachment,
    Company,
    Contact,
    Customer,
    Employee,
    Job,
    JobNote,
    ProjectStatusCode,
    Quote,
    Site,
)
from simpro_client.client import SimproClient

GET_CASES = [
    ("companies", 1, {}, "/companies/1", {"ID": 1, "Name": "CVC"}, Company),
    (
        "customers",
        2,
        {"company_id": 1},
        "/companies/1/customers/2",
        {
            "ID": 2,
            "CompanyID": 1,
            "GivenName": "Ada",
            "FamilyName": "Lovelace",
        },
        Customer,
    ),
    (
        "jobs",
        3,
        {"company_id": 1},
        "/companies/1/jobs/3",
        {
            "ID": 3,
            "CompanyID": 1,
            "Name": "Service",
            "Status": "Open",
            "Total": 10.0,
        },
        Job,
    ),
    (
        "quotes",
        4,
        {"company_id": 1},
        "/companies/1/quotes/4",
        {
            "ID": 4,
            "CompanyID": 1,
            "Name": "Quote",
            "Status": "Draft",
            "Total": 20.0,
        },
        Quote,
    ),
    (
        "contacts",
        5,
        {"company_id": 1, "customer_id": 2},
        "/companies/1/customers/2/contacts/5",
        {
            "ID": 5,
            "CompanyID": 1,
            "CustomerID": 2,
            "GivenName": "Grace",
            "FamilyName": "Hopper",
        },
        Contact,
    ),
    (
        "sites",
        6,
        {"company_id": 1},
        "/companies/1/sites/6",
        {"ID": 6, "CompanyID": 1, "CustomerID": 2, "Name": "Plant"},
        Site,
    ),
    (
        "assets",
        7,
        {"company_id": 1, "site_id": 6},
        "/companies/1/sites/6/assets/7",
        {
            "ID": 7,
            "CompanyID": 1,
            "SiteID": 6,
            "AssetNo": "A-7",
            "Name": "Pump",
        },
        Asset,
    ),
    (
        "employees",
        8,
        {"company_id": 1},
        "/companies/1/employees/8",
        {"ID": 8, "Name": "Linus Torvalds"},
        Employee,
    ),
    (
        "job_notes",
        10,
        {"company_id": 1, "job_id": 3},
        "/companies/1/jobs/3/notes/10",
        {
            "ID": 10,
            "Reference": {"Text": "Job #3"},
            "Visibility": {"Admin": True, "Customer": False},
        },
        JobNote,
    ),
    # ``item_id`` is a string here on purpose: Attachment.ID is a string
    # upstream, which is why ``get()`` takes ``int | str``.
    (
        "attachments",
        "11",
        {"company_id": 1, "job_id": 3},
        "/companies/1/jobs/3/attachments/files/11",
        {"ID": "11", "Filename": "photo.jpg"},
        Attachment,
    ),
    (
        "project_status_codes",
        12,
        {"company_id": 1},
        "/companies/1/setup/statusCodes/projects/12",
        {"ID": 12, "Name": "Open"},
        ProjectStatusCode,
    ),
]


def mock_token(mock_settings):
    respx.post(mock_settings.token_url).mock(
        return_value=Response(200, json={"access_token": "tok", "expires_in": 3600})
    )


@pytest.mark.parametrize(
    ("resource", "item_id", "scope", "path", "payload", "model_type"), GET_CASES
)
@respx.mock
def test_get_by_id_uses_exact_route_and_model(
    mock_settings, resource, item_id, scope, path, payload, model_type
):
    mock_token(mock_settings)
    route = respx.get(f"{mock_settings.base_url}{path}").mock(
        return_value=Response(200, json=payload)
    )

    with SimproClient(settings=mock_settings) as client:
        result = getattr(client, resource).get(item_id, **scope)

    assert route.called
    assert isinstance(result, model_type)


@respx.mock
def test_page_preserves_headers_filters_and_company_selection(mock_settings):
    mock_token(mock_settings)
    route = respx.get(f"{mock_settings.base_url}/companies/2/jobs/").mock(
        return_value=Response(
            200,
            json=[
                {
                    "ID": 3,
                    "CompanyID": 2,
                    "Name": "Service",
                    "Status": "Open",
                    "DateIssued": "2026-09-07",
                    "Total": 10.0,
                }
            ],
            headers={
                "Result-Total": "5",
                "Result-Count": "1",
                "Result-Pages": "3",
            },
        )
    )

    with SimproClient(settings=mock_settings) as client:
        result = client.jobs.fetch_page(
            company_id=2,
            page=2,
            page_size=2,
            filters={"Status": "Open"},
        )

    request = route.calls.last.request
    assert request.url.params["Status"] == "Open"
    assert request.url.params["page"] == "2"
    assert request.url.params["pageSize"] == "2"
    assert isinstance(result.items[0], Job)
    assert (result.total, result.count, result.pages) == (5, 1, 3)


def test_missing_nested_scope_fails_before_request(mock_settings):
    with SimproClient(settings=mock_settings) as client:
        with pytest.raises(ValueError, match="site_id"):
            client.assets.get(7, company_id=1)


@respx.mock
def test_columns_are_sent_as_csv_on_collections(mock_settings):
    """``columns=`` reaches the wire as Simpro's csv query parameter.

    Collection routes return a narrow default projection without it, so the
    client has to be able to ask for more (ADR-013 §5).
    """
    mock_token(mock_settings)
    route = respx.get(f"{mock_settings.base_url}/companies/2/jobs/").mock(
        return_value=Response(
            200,
            json=[
                {"ID": 3, "CompanyID": 2, "Name": "S", "Status": "Open", "Total": 1.0}
            ],
            headers={
                "Result-Total": "1",
                "Result-Count": "1",
                "Result-Pages": "1",
            },
        )
    )

    with SimproClient(settings=mock_settings) as client:
        client.jobs.fetch_page(company_id=2, columns=["ID", "Name", "Status"])

    assert route.calls.last.request.url.params["columns"] == "ID,Name,Status"


@respx.mock
def test_columns_are_sent_on_detail_routes_too(mock_settings):
    """Simpro accepts ``columns`` on detail routes, so ``get()`` sends it."""
    mock_token(mock_settings)
    detail = respx.get(f"{mock_settings.base_url}/companies/1").mock(
        return_value=Response(200, json={"ID": 1, "Name": "CVC"})
    )

    with SimproClient(settings=mock_settings) as client:
        client.companies.get(1, columns=["ID", "Name"])

    assert detail.calls.last.request.url.params["columns"] == "ID,Name"


@respx.mock
def test_omitting_columns_sends_no_columns_parameter(mock_settings):
    """Without ``columns`` the client must not invent one."""
    mock_token(mock_settings)
    detail = respx.get(f"{mock_settings.base_url}/companies/1").mock(
        return_value=Response(200, json={"ID": 1, "Name": "CVC"})
    )

    with SimproClient(settings=mock_settings) as client:
        client.companies.get(1)

    assert "columns" not in detail.calls.last.request.url.params


@pytest.mark.parametrize("page_size", [0, -1, 251, 1000])
def test_page_size_outside_the_documented_range_is_rejected(mock_settings, page_size):
    """``pageSize`` is ``minimum 1, maximum 250`` in the spec.

    Rejected before any request, so an out-of-range value never reaches the
    server as a 4xx.
    """
    with (
        SimproClient(settings=mock_settings) as client,
        pytest.raises(ValueError, match="page_size must be between 1 and 250"),
    ):
        client.jobs.fetch_page(company_id=1, page_size=page_size)


def test_page_below_one_is_rejected(mock_settings):
    """Simpro pages are 1-based."""
    with (
        SimproClient(settings=mock_settings) as client,
        pytest.raises(ValueError, match="page must be >= 1"),
    ):
        client.jobs.fetch_page(company_id=1, page=0)
