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
    Project,
    Quote,
    Site,
    Status,
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
        {
            "ID": 8,
            "CompanyID": 1,
            "GivenName": "Linus",
            "FamilyName": "Torvalds",
        },
        Employee,
    ),
    (
        "projects",
        9,
        {"company_id": 2},
        "/companies/2/projects/9",
        {
            "ID": 9,
            "CompanyID": 2,
            "CustomerID": 2,
            "Name": "Upgrade",
            "Status": "Active",
            "Total": 1000.0,
        },
        Project,
    ),
    (
        "job_notes",
        10,
        {"company_id": 1, "job_id": 3},
        "/companies/1/jobs/3/notes/10",
        {"ID": 10, "JobID": 3},
        JobNote,
    ),
    (
        "attachments",
        11,
        {"company_id": 1, "job_id": 3},
        "/companies/1/jobs/3/attachments/11",
        {"ID": 11, "JobID": 3, "Filename": "photo.jpg"},
        Attachment,
    ),
    (
        "statuses",
        12,
        {"company_id": 1},
        "/companies/1/statuses/12",
        {
            "ID": 12,
            "CompanyID": 1,
            "Name": "Open",
            "IsDefault": True,
        },
        Status,
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
