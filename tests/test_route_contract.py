"""Declarative guard for the committed read-only route inventory."""

from simpro_client.endpoints import (
    AssetsEndpoint,
    AttachmentsEndpoint,
    CompaniesEndpoint,
    ContactsEndpoint,
    CustomersEndpoint,
    EmployeesEndpoint,
    JobNotesEndpoint,
    JobsEndpoint,
    ProjectsEndpoint,
    QuotesEndpoint,
    SitesEndpoint,
    StatusesEndpoint,
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
    ProjectsEndpoint: (
        "/companies/{company_id}/projects/",
        "/companies/{company_id}/projects/{project_id}",
    ),
    JobNotesEndpoint: (
        "/companies/{company_id}/jobs/{job_id}/notes/",
        "/companies/{company_id}/jobs/{job_id}/notes/{note_id}",
    ),
    AttachmentsEndpoint: (
        "/companies/{company_id}/jobs/{job_id}/attachments/",
        "/companies/{company_id}/jobs/{job_id}/attachments/{attachment_id}",
    ),
    StatusesEndpoint: (
        "/companies/{company_id}/statuses/",
        "/companies/{company_id}/statuses/{status_id}",
    ),
}


def test_all_route_templates_match_the_committed_contract():
    for endpoint_type, expected in EXPECTED_ROUTES.items():
        assert (endpoint_type.collection_path, endpoint_type.detail_path) == expected