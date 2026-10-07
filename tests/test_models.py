"""Contract tests for typed Simpro resources."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from simpro_client.models import (
    Asset,
    Attachment,
    Company,
    CompanyCustomer,
    Contact,
    CustomerSummary,
    Employee,
    IndividualCustomer,
    Job,
    JobNote,
    ProjectStatusCode,
    Quote,
    Site,
)

#: Payloads addressed by model, so the temporal test below never depends on
#: list position. Resizing MODEL_CASES used to silently change what it
#: asserted (ADR-013 re-shape; see tests/CLAUDE.md §7).
MODEL_CASES = [
    (
        Company,
        {
            "ID": 1,
            "Name": "CVC",
            "Address": {"Line1": "Ground floor", "Line2": "31 McKechnie Dr"},
            "Phone": "03 9000 0000",
            "Timezone": "Australia/Melbourne",
            "ScheduleFormat": 30,
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "Name",
        ["Address", "Phone", "Timezone", "ScheduleFormat", "DateModified"],
    ),
    (
        CustomerSummary,
        {
            "ID": 2,
            "Type": "Individual",
            "CompanyName": "",
            "GivenName": "Ada",
            "FamilyName": "Lovelace",
            "_href": "/api/v1.0/companies/1/customers/individuals/2",
        },
        "Type",
        [],
    ),
    (
        IndividualCustomer,
        {
            "ID": 2,
            "Type": "Individual",
            "GivenName": "Ada",
            "FamilyName": "Lovelace",
            "Title": "Ms",
            "Email": "ada@example.test",
            "Phone": "555-0100",
            "CellPhone": "0400000000",
            "AmountOwing": "1234.55",
            "Address": {
                "Address": "1 Main St",
                "City": "Melbourne",
                "State": "VIC",
                "PostalCode": "3000",
                "Country": "AU",
            },
            "Sites": [{"ID": 6, "Name": "Plant"}],
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "GivenName",
        [
            "Title",
            "Email",
            "Phone",
            "CellPhone",
            "AmountOwing",
            "Address",
            "Sites",
            "DateModified",
        ],
    ),
    (
        CompanyCustomer,
        {
            "ID": 3,
            "Type": "Company",
            "CompanyName": "Acme Pty Ltd",
            "CompanyNumber": "ACN 123",
            "EIN": "",
            "Email": "accounts@acme.test",
            "Phone": "555-0200",
            "Website": "https://acme.test",
            "AmountOwing": "0.00",
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "CompanyName",
        [
            "CompanyNumber",
            "EIN",
            "Email",
            "Phone",
            "Website",
            "AmountOwing",
            "DateModified",
        ],
    ),
    (
        Job,
        {
            "ID": 3,
            "CompanyID": 1,
            "Name": "Service",
            "Status": "Open",
            "DateIssued": "2026-09-07",
            "Total": 120.5,
        },
        "Status",
        ["DateIssued"],
    ),
    (
        Quote,
        {
            "ID": 4,
            "CompanyID": 1,
            "CustomerID": 2,
            "Name": "Quote",
            "Status": "Draft",
            "Total": 99.0,
        },
        "Name",
        ["CustomerID"],
    ),
    (
        Contact,
        {
            "ID": 5,
            "GivenName": "Grace",
            "FamilyName": "Hopper",
            "Title": "Dr",
            "Position": "Engineer",
            "Department": "Engineering",
            "Email": "grace@example.test",
            "WorkPhone": "555-0101",
            "CellPhone": "0400000001",
            "AltPhone": "",
            "Fax": "",
            "Notes": "",
            "JobContact": True,
            "PrimaryJobContact": False,
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "FamilyName",
        [
            "Title",
            "Position",
            "Department",
            "Email",
            "WorkPhone",
            "CellPhone",
            "AltPhone",
            "Fax",
            "Notes",
            "JobContact",
            "PrimaryJobContact",
            "DateModified",
        ],
    ),
    (
        Site,
        {
            "ID": 6,
            "Name": "Plant",
            "Address": {
                "Address": "1 Main St",
                "City": "Melbourne",
                "State": "VIC",
                "PostalCode": "3000",
                "Country": "AU",
            },
            "BillingAddress": {
                "Address": "PO Box 9",
                "City": "Melbourne",
                "State": "VIC",
                "PostalCode": "3001",
            },
            "Customers": [
                {
                    "ID": 2,
                    "Type": "Individual",
                    "CompanyName": "",
                    "GivenName": "Ada",
                    "FamilyName": "Lovelace",
                }
            ],
            "Zone": {"ID": 1, "Name": "Metro North"},
            "PublicNotes": "",
            "PrivateNotes": "",
            "Archived": False,
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "Name",
        [
            "Address",
            "BillingAddress",
            "Customers",
            "Zone",
            "PublicNotes",
            "PrivateNotes",
            "Archived",
            "DateModified",
        ],
    ),
    (
        Asset,
        {
            "ID": 7,
            "CompanyID": 1,
            "SiteID": 6,
            "AssetNo": "A-7",
            "Name": "Pump",
            "SerialNo": "SN-7",
            "Model": "M1",
            "Manufacturer": "Maker",
            "InstalledDate": "2026-01-02",
        },
        "AssetNo",
        ["SerialNo", "Model", "Manufacturer", "InstalledDate"],
    ),
    (
        Employee,
        {
            "ID": 8,
            "Name": "Linus Torvalds",
            "Position": "Engineer",
            "PrimaryContact": {
                "Email": "linus@example.test",
                "SecondaryEmail": "",
                "WorkPhone": "555-0102",
                "CellPhone": "0400000000",
                "Extension": "",
                "Fax": "",
                "PreferredNotificationMethod": "Email",
            },
            "Address": {
                "Address": "1 Main St",
                "City": "Melbourne",
                "State": "VIC",
                "PostalCode": "3000",
                "Country": "AU",
            },
            "Zones": [{"ID": 1, "Name": "Metro"}],
            "DefaultZone": {"ID": 1, "Name": "Metro"},
            "DefaultCompany": {"ID": 1, "Name": "CVC"},
            "Archived": False,
            "DateCreated": "2026-01-02T09:00:00+10:00",
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "Name",
        [
            "Position",
            "PrimaryContact",
            "Address",
            "Zones",
            "DefaultZone",
            "DefaultCompany",
            "Archived",
            "DateCreated",
            "DateModified",
        ],
    ),
    (
        JobNote,
        {
            "ID": 10,
            "Reference": {"Text": "Job #3", "Number": "3", "Type": "Job"},
            "Visibility": {"Admin": True, "Customer": False},
            "Subject": "Visit",
            "Note": "Completed",
            "DateCreated": "2026-09-07T10:30:00+10:00",
            "FollowUpDate": "2026-09-14",
            "Attachments": [{"FileName": "photo.jpg", "_href": "/api/v1.0/x"}],
            "SubmittedBy": {
                "ID": 8,
                "Name": "Linus Torvalds",
                "Type": "employee",
                "TypeId": 8,
            },
            "AssignTo": None,
        },
        "Reference",
        [
            "Subject",
            "Note",
            "DateCreated",
            "FollowUpDate",
            "Attachments",
            "SubmittedBy",
            "AssignTo",
        ],
    ),
    (
        Attachment,
        {
            "ID": "11",
            "Filename": "photo.jpg",
            "MimeType": "image/jpeg",
            "FileSizeBytes": 2048,
            "DateAdded": "2026-09-07T10:31:00+10:00",
            "Public": False,
            "Email": False,
            "Folder": None,
            "AddedBy": {
                "ID": 8,
                "Name": "Linus Torvalds",
                "Type": "employee",
                "TypeId": 8,
            },
        },
        "Filename",
        [
            "MimeType",
            "FileSizeBytes",
            "DateAdded",
            "Public",
            "Email",
            "Folder",
            "AddedBy",
        ],
    ),
    (
        ProjectStatusCode,
        {
            "ID": 12,
            "Name": "Open",
            "Color": "#ff0000",
            "Priority": 10,
            "DateModified": "2026-09-07T10:30:00+10:00",
        },
        "Name",
        ["Color", "Priority", "DateModified"],
    ),
]


PAYLOADS = {case[0]: case[1] for case in MODEL_CASES}


@pytest.mark.parametrize(
    ("model_type", "payload", "required_alias", "optional_aliases"),
    MODEL_CASES,
    ids=[case[0].__name__ for case in MODEL_CASES],
)
def test_models_accept_aliases_and_ignore_unknown_fields(
    model_type, payload, required_alias, optional_aliases
):
    with_extra = {**payload, "FutureAPIField": "ignored"}
    model = model_type.model_validate(with_extra)

    assert model.id == payload["ID"]
    assert not hasattr(model, "FutureAPIField")
    assert model_type.model_validate(model.model_dump()).id == payload["ID"]

    missing_required = payload.copy()
    missing_required.pop(required_alias)
    with pytest.raises(ValidationError):
        model_type.model_validate(missing_required)

    without_optional = payload.copy()
    for alias in optional_aliases:
        without_optional.pop(alias)
    model_type.model_validate(without_optional)


def test_temporal_fields_use_python_types():
    """Date and timestamp aliases parse into Python types, not strings."""
    assert isinstance(Job.model_validate(PAYLOADS[Job]).date_issued, date)
    assert isinstance(Asset.model_validate(PAYLOADS[Asset]).installed_date, date)
    assert isinstance(JobNote.model_validate(PAYLOADS[JobNote]).date_created, datetime)
    assert isinstance(
        JobNote.model_validate(PAYLOADS[JobNote]).follow_up_date, date
    )
    assert isinstance(
        Attachment.model_validate(PAYLOADS[Attachment]).date_added, datetime
    )
