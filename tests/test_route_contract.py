"""Declarative guard for the committed read-only route inventory.

Changing an expected value here is a contract change and must be explained in
the sprint report (`tests/CLAUDE.md` §7). The routes below come from Simpro's
published spec, vendored at `docs/contracts/simpro-openapi-v1-get-subset.json`
(ADR-013), not from the mock.
"""

import pytest

from simpro_client.endpoints import (
    AssetsEndpoint,
    AttachmentsEndpoint,
    CompaniesEndpoint,
    ContactsEndpoint,
    CustomersEndpoint,
    EmployeesEndpoint,
    JobNotesEndpoint,
    JobsEndpoint,
    ProjectStatusCodesEndpoint,
    QuotesEndpoint,
    ResourceEndpoint,
    SitesEndpoint,
)

EXPECTED_ROUTES = {
    CompaniesEndpoint: ("/companies/", "/companies/{company_id}"),
    CustomersEndpoint: (
        "/companies/{company_id}/customers/",
        "/companies/{company_id}/customers/{customer_id}",
    ),
    JobsEndpoint: (
        "/companies/{company_id}/jobs/",
        "/companies/{company_id}/jobs/{job_id}",
    ),
    QuotesEndpoint: (
        "/companies/{company_id}/quotes/",
        "/companies/{company_id}/quotes/{quote_id}",
    ),
    ContactsEndpoint: (
        "/companies/{company_id}/customers/{customer_id}/contacts/",
        "/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}",
    ),
    SitesEndpoint: (
        "/companies/{company_id}/sites/",
        "/companies/{company_id}/sites/{site_id}",
    ),
    AssetsEndpoint: (
        "/companies/{company_id}/sites/{site_id}/assets/",
        "/companies/{company_id}/sites/{site_id}/assets/{asset_id}",
    ),
    EmployeesEndpoint: (
        "/companies/{company_id}/employees/",
        "/companies/{company_id}/employees/{employee_id}",
    ),
    JobNotesEndpoint: (
        "/companies/{company_id}/jobs/{job_id}/notes/",
        "/companies/{company_id}/jobs/{job_id}/notes/{note_id}",
    ),
    AttachmentsEndpoint: (
        "/companies/{company_id}/jobs/{job_id}/attachments/files/",
        "/companies/{company_id}/jobs/{job_id}/attachments/files/{file_id}",
    ),
    ProjectStatusCodesEndpoint: (
        "/companies/{company_id}/setup/statusCodes/projects/",
        "/companies/{company_id}/setup/statusCodes/projects/{status_code_id}",
    ),
}


@pytest.mark.parametrize("endpoint_type", EXPECTED_ROUTES, ids=lambda cls: cls.__name__)
def test_route_templates_match_the_committed_contract(
    endpoint_type: type[ResourceEndpoint],
) -> None:
    """Each endpoint's paths match the vendored contract.

    Parametrized rather than looped so a mismatch reports every offending
    endpoint, not just the first.
    """
    expected = EXPECTED_ROUTES[endpoint_type]
    assert (endpoint_type.collection_path, endpoint_type.detail_path) == expected


@pytest.mark.parametrize("endpoint_type", EXPECTED_ROUTES, ids=lambda cls: cls.__name__)
def test_item_key_appears_in_the_detail_path(
    endpoint_type: type[ResourceEndpoint],
) -> None:
    """``item_key`` names a placeholder that ``detail_path`` actually has.

    Nothing else checks this. A stale ``item_key`` after a route change would
    otherwise surface only as a ``ValueError`` from ``ResourceEndpoint._render``
    in whichever test happened to call ``get()``.
    """
    placeholder = "{" + endpoint_type.item_key + "}"
    assert placeholder in endpoint_type.detail_path, (
        f"{endpoint_type.__name__}.item_key is {endpoint_type.item_key!r}, "
        f"which does not appear in {endpoint_type.detail_path!r}"
    )


def test_contract_covers_every_registered_endpoint() -> None:
    """``EXPECTED_ROUTES`` lists every endpoint class the package exports.

    Guards against a new endpoint being added without a contract entry, which
    the hand-written dict would otherwise not notice.
    """
    import simpro_client.endpoints as endpoints_module

    exported = {
        getattr(endpoints_module, name)
        for name in endpoints_module.__all__
        if name.endswith("Endpoint") and name != "ResourceEndpoint"
    }
    assert exported == set(EXPECTED_ROUTES), (
        f"missing from EXPECTED_ROUTES: "
        f"{sorted(cls.__name__ for cls in exported - set(EXPECTED_ROUTES))}; "
        f"stale entries: "
        f"{sorted(cls.__name__ for cls in set(EXPECTED_ROUTES) - exported)}"
    )
