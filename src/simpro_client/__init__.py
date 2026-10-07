"""Simpro API Client: reusable integration layer for the Simpro REST API."""

from simpro_client.client import SimproClient
from simpro_client.config import SimproSettings, get_settings
from simpro_client.endpoints import Page
from simpro_client.models import (
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

__all__ = [
    "Asset",
    "Attachment",
    "Company",
    "Contact",
    "Customer",
    "Employee",
    "Job",
    "JobNote",
    "Page",
    "ProjectStatusCode",
    "Quote",
    "SimproClient",
    "SimproSettings",
    "Site",
    "get_settings",
]
__version__ = "0.1.0"
