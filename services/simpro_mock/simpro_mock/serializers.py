"""Compose wire-shaped response dicts from flat ORM rows.

Simpro returns composite values as nested objects (``Employee.PrimaryContact``,
``Company.Address``) and returns a *narrow* projection from collection routes
but a wide one from detail routes. The database stores those values flat, one
column each, because that is what keeps schema churn bounded across the
ADR-013 re-shape.

This module is the single place that bridges the two. Before it, every response
was hand-built inline in ``routers.py`` — twice per resource, once for the list
leg and once for the detail leg — so one renamed field meant editing 24
construction sites. Now each resource has one ``*_list_dict`` and one
``*_detail_dict``, and ``routers.py`` calls them.

Field names here are the wire contract and must match
``docs/contracts/simpro-openapi-v1-get-subset.json``. The matching Pydantic
classes in ``schemas.py`` stay on each route's ``response_model``, so a typo
here fails the request rather than silently serving a wrong shape.
"""

from typing import Any

from simpro_mock.models import Attachment, Company, Employee, JobNote, Status, Zone


def _named_ref(row: Zone | Company | None) -> dict[str, Any] | None:
    """Render an ``{"ID", "Name"}`` reference, or ``None`` when absent."""
    if row is None:
        return None
    return {"ID": row.id, "Name": row.name}


def _staff_ref(employee: Employee | None) -> dict[str, Any] | None:
    """Render a staff reference, or ``None`` when absent.

    ``Type`` is always ``"employee"`` here: the mock models only employees, not
    the contractor and plant staff kinds Simpro also allows.
    """
    if employee is None:
        return None
    return {
        "ID": employee.id,
        "Name": employee.name,
        "Type": "employee",
        "TypeId": employee.id,
    }


# ---------------------------------------------------------------- companies


def company_list_dict(company: Company) -> dict[str, Any]:
    """The two fields Simpro's company collection route returns."""
    return {"ID": company.id, "Name": company.name}


def company_detail_dict(company: Company) -> dict[str, Any]:
    """Every documented company configuration field.

    ``Banking`` is omitted by ADR-013's fidelity scope. ``DefaultCostCenter``
    is nullable upstream and the mock has no cost centres, so it is ``None``.
    """
    return {
        "ID": company.id,
        "Name": company.name,
        "Address": {
            "Line1": company.address_line1,
            "Line2": company.address_line2,
        },
        "BillingAddress": {
            "Line1": company.billing_address_line1,
            "Line2": company.billing_address_line2,
        },
        "Phone": company.phone,
        "Fax": company.fax,
        "Email": company.email,
        "Website": company.website,
        "Country": company.country,
        "Currency": company.currency,
        "Timezone": company.timezone,
        "TimezoneOffset": company.timezone_offset,
        "CompanyNo": company.company_no,
        "EIN": company.ein,
        "EmployerTaxRefNo": company.employer_tax_ref_no,
        "CISCertNo": company.cis_cert_no,
        "Licence": company.licence,
        "TaxName": company.tax_name,
        "DefaultLanguage": company.default_language,
        "DefaultCostCenter": None,
        "SingleCostCenterMode": company.single_cost_center_mode,
        "SimproPayments": company.simpro_payments,
        "Template": company.template,
        "MultiCompanyLabel": company.multi_company_label,
        "MultiCompanyColor": company.multi_company_color,
        "ScheduleFormat": company.schedule_format,
        "UIDateFormat": company.ui_date_format,
        "UITimeFormat": company.ui_time_format,
        "DateModified": company.date_modified.isoformat(),
    }


# ---------------------------------------------------------------- employees


def employee_list_dict(employee: Employee) -> dict[str, Any]:
    """The two fields Simpro's employee collection route returns."""
    return {"ID": employee.id, "Name": employee.name}


def employee_detail_dict(employee: Employee) -> dict[str, Any]:
    """An employee's documented detail fields.

    ``Banking`` and ``PayRates`` are omitted by ADR-013's fidelity scope.
    ``Zones`` carries the employee's default zone only: the mock models one
    zone per employee, so there is no wider membership to report.
    """
    zone = _named_ref(employee.default_zone)
    return {
        "ID": employee.id,
        "Name": employee.name,
        "Position": employee.position,
        "PrimaryContact": {
            "Email": employee.email,
            "SecondaryEmail": employee.secondary_email,
            "WorkPhone": employee.work_phone,
            "CellPhone": employee.cell_phone,
            "Extension": employee.extension,
            "Fax": employee.fax,
            "PreferredNotificationMethod": employee.preferred_notification_method,
        },
        "Address": {
            "Address": employee.address,
            "City": employee.city,
            "State": employee.state,
            "PostalCode": employee.postal_code,
            "Country": employee.country,
        },
        "Zones": [zone] if zone else [],
        "DefaultZone": zone,
        "DefaultCompany": _named_ref(employee.company),
        "Archived": employee.archived,
        "DateCreated": employee.date_created.isoformat(),
        "DateModified": employee.date_modified.isoformat(),
    }


# -------------------------------------------------------------- attachments


def attachment_list_dict(attachment: Attachment) -> dict[str, Any]:
    """The two fields Simpro's attachment collection route returns."""
    return {"ID": attachment.id, "Filename": attachment.filename}


def attachment_detail_dict(attachment: Attachment) -> dict[str, Any]:
    """An attachment's documented detail fields.

    ``Folder`` is nullable upstream and the mock has no folder hierarchy, so it
    is ``None``.
    """
    return {
        "ID": attachment.id,
        "Filename": attachment.filename,
        "MimeType": attachment.mime_type,
        "FileSizeBytes": attachment.file_size_bytes,
        "DateAdded": attachment.date_added.isoformat(),
        "Public": attachment.public,
        "Email": attachment.email,
        "Folder": None,
        "AddedBy": _staff_ref(attachment.added_by),
    }


# ---------------------------------------------------------------- job notes


def _note_reference(note: JobNote) -> dict[str, Any]:
    """Render a note's ``Reference`` object. Only ``Text`` is required."""
    return {
        "Text": note.reference_text,
        "Number": note.reference_number,
        "Type": note.reference_type,
    }


def _note_visibility(note: JobNote) -> dict[str, Any]:
    """Render a note's ``Visibility`` object. Both members are required."""
    return {"Admin": note.visibility_admin, "Customer": note.visibility_customer}


def job_note_list_dict(note: JobNote) -> dict[str, Any]:
    """The fields Simpro's job-note collection route returns."""
    return {
        "ID": note.id,
        "Subject": note.subject,
        "Reference": _note_reference(note),
        "Visibility": _note_visibility(note),
    }


def job_note_detail_dict(note: JobNote) -> dict[str, Any]:
    """A job note's documented detail fields.

    ``Attachments`` is a required array, and an empty one is legal: the spec
    requires the key and its type, not a non-empty list. The mock attaches
    files to jobs rather than to individual notes, so it is always empty.
    """
    return {
        "ID": note.id,
        "Subject": note.subject,
        "Note": note.note,
        "Reference": _note_reference(note),
        "Visibility": _note_visibility(note),
        "DateCreated": note.date_created.isoformat(),
        "FollowUpDate": (
            note.follow_up_date.isoformat() if note.follow_up_date else None
        ),
        "Attachments": [],
        "SubmittedBy": _staff_ref(note.submitted_by),
        "AssignTo": _staff_ref(note.assign_to),
    }


# ----------------------------------------------------- project status codes


def project_status_code_list_dict(status: Status) -> dict[str, Any]:
    """The two fields Simpro's status-code collection route returns."""
    return {"ID": status.id, "Name": status.name}


def project_status_code_detail_dict(status: Status) -> dict[str, Any]:
    """A project status code's documented detail fields."""
    return {
        "ID": status.id,
        "Name": status.name,
        "Color": status.color,
        "Priority": status.priority,
        "DateModified": status.date_modified.isoformat(),
    }
