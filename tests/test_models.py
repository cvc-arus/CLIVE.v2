"""Contract tests for typed Simpro resources."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from simpro_client.models import (
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

MODEL_CASES = [
    (Company, {"ID": 1, "Name": "CVC"}, "Name", []),
    (
        Customer,
        {
            "ID": 2,
            "CompanyID": 1,
            "GivenName": "Ada",
            "FamilyName": "Lovelace",
            "Email": "ada@example.test",
            "Phone": "555-0100",
        },
        "GivenName",
        ["Email", "Phone"],
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
            "CompanyID": 1,
            "CustomerID": 2,
            "GivenName": "Grace",
            "FamilyName": "Hopper",
            "Position": "Engineer",
            "Email": "grace@example.test",
            "Phone": "555-0101",
        },
        "FamilyName",
        ["Position", "Email", "Phone"],
    ),
    (
        Site,
        {
            "ID": 6,
            "CompanyID": 1,
            "CustomerID": 2,
            "Name": "Plant",
            "Address": "1 Main St",
            "City": "Melbourne",
            "Postcode": "3000",
            "State": "VIC",
            "Country": "AU",
        },
        "Name",
        ["Address", "City", "Postcode", "State", "Country"],
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
            "CompanyID": 1,
            "GivenName": "Linus",
            "FamilyName": "Torvalds",
            "Position": "Engineer",
            "Email": "linus@example.test",
            "Phone": "555-0102",
        },
        "GivenName",
        ["Position", "Email", "Phone"],
    ),
    (
        Project,
        {
            "ID": 9,
            "CompanyID": 2,
            "CustomerID": 2,
            "SiteID": 6,
            "Name": "Upgrade",
            "Status": "Active",
            "Total": 1000.0,
        },
        "CustomerID",
        ["SiteID"],
    ),
    (
        JobNote,
        {
            "ID": 10,
            "JobID": 3,
            "Subject": "Visit",
            "Note": "Completed",
            "CreatedBy": 8,
            "CreatedAt": "2026-09-07T10:30:00",
        },
        "JobID",
        ["Subject", "Note", "CreatedBy", "CreatedAt"],
    ),
    (
        Attachment,
        {
            "ID": 11,
            "JobID": 3,
            "Filename": "photo.jpg",
            "MimeType": "image/jpeg",
            "FileSize": 2048,
            "UploadedAt": "2026-09-07T10:31:00",
        },
        "Filename",
        ["MimeType", "FileSize", "UploadedAt"],
    ),
    (
        Status,
        {
            "ID": 12,
            "CompanyID": 1,
            "Name": "Open",
            "Category": "Job",
            "IsDefault": True,
        },
        "IsDefault",
        ["Category"],
    ),
]


@pytest.mark.parametrize(
    ("model_type", "payload", "required_alias", "optional_aliases"), MODEL_CASES
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
    assert isinstance(Job.model_validate(MODEL_CASES[2][1]).date_issued, date)
    assert isinstance(Asset.model_validate(MODEL_CASES[6][1]).installed_date, date)
    assert isinstance(JobNote.model_validate(MODEL_CASES[9][1]).created_at, datetime)
    assert isinstance(
        Attachment.model_validate(MODEL_CASES[10][1]).uploaded_at, datetime
    )
