"""Simpro API Client: reusable integration layer for the Simpro REST API."""

from simpro_client.client import SimproClient
from simpro_client.config import SimproSettings, get_settings
from simpro_client.endpoints import Page
from simpro_client.models import (
    AddressBlock,
    Asset,
    Attachment,
    Company,
    CompanyAddress,
    Contact,
    Customer,
    Employee,
    EmployeeContact,
    Job,
    JobNote,
    NamedRef,
    NoteAttachment,
    NoteReference,
    NoteVisibility,
    ProjectStatusCode,
    Quote,
    Site,
    StaffRef,
)

__all__ = [
    "AddressBlock",
    "Asset",
    "Attachment",
    "Company",
    "CompanyAddress",
    "Contact",
    "Customer",
    "Employee",
    "EmployeeContact",
    "Job",
    "JobNote",
    "NamedRef",
    "NoteAttachment",
    "NoteReference",
    "NoteVisibility",
    "Page",
    "ProjectStatusCode",
    "Quote",
    "SimproClient",
    "SimproSettings",
    "Site",
    "StaffRef",
    "get_settings",
]
__version__ = "0.1.0"
