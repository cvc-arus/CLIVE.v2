from simpro_client.endpoints.asset import AssetsEndpoint
from simpro_client.endpoints.attachment import AttachmentsEndpoint
from simpro_client.endpoints.base import Page, ResourceEndpoint
from simpro_client.endpoints.company import CompaniesEndpoint
from simpro_client.endpoints.contact import ContactsEndpoint
from simpro_client.endpoints.customer import (
    CompanyCustomersEndpoint,
    CustomersEndpoint,
    IndividualCustomersEndpoint,
)
from simpro_client.endpoints.employee import EmployeesEndpoint
from simpro_client.endpoints.job import JobsEndpoint
from simpro_client.endpoints.job_note import JobNotesEndpoint
from simpro_client.endpoints.project_status_code import ProjectStatusCodesEndpoint
from simpro_client.endpoints.quote import QuotesEndpoint
from simpro_client.endpoints.site import SitesEndpoint

__all__ = [
    "AssetsEndpoint",
    "AttachmentsEndpoint",
    "CompaniesEndpoint",
    "CompanyCustomersEndpoint",
    "ContactsEndpoint",
    "CustomersEndpoint",
    "EmployeesEndpoint",
    "IndividualCustomersEndpoint",
    "JobNotesEndpoint",
    "JobsEndpoint",
    "Page",
    "ProjectStatusCodesEndpoint",
    "QuotesEndpoint",
    "ResourceEndpoint",
    "SitesEndpoint",
]
