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

from simpro_mock.models import (
    Attachment,
    Company,
    Contact,
    Customer,
    CustomFieldValue,
    Employee,
    JobNote,
    Site,
    Status,
    Zone,
)


def _named_ref(row: Zone | Company | Site | None) -> dict[str, Any] | None:
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


# ---------------------------------------------------------------- customers


def _custom_fields(values: list[CustomFieldValue]) -> list[dict[str, Any]]:
    """Render a record's custom fields as the contract's paired shape.

    ``ListItems`` is stored newline-separated and is only meaningful for a
    ``List`` field; it is ``None`` otherwise, which the contract allows.
    """
    rendered = []
    for value in values:
        definition = value.custom_field
        rendered.append(
            {
                "CustomField": {
                    "ID": definition.id,
                    "Name": definition.name,
                    "Type": definition.field_type,
                    "IsMandatory": definition.is_mandatory,
                    "ListItems": (
                        definition.list_items.splitlines()
                        if definition.list_items
                        else None
                    ),
                },
                "Value": value.value,
            }
        )
    return rendered


def _address(row: Customer | Site) -> dict[str, Any]:
    """Render a five-member address block from flat columns."""
    return {
        "Address": row.address,
        "City": row.city,
        "State": row.state,
        "PostalCode": row.postal_code,
        "Country": row.country,
    }


def _customer_ref(customer: Customer) -> dict[str, Any]:
    """Render a customer as it appears nested in another resource.

    Carries both name shapes: ``Type`` tells the caller which one matters.
    """
    return {
        "ID": customer.id,
        "Type": customer.type,
        "CompanyName": customer.company_name,
        "GivenName": customer.given_name,
        "FamilyName": customer.family_name,
    }


def customer_summary_dict(customer: Customer) -> dict[str, Any]:
    """Render a row of the polymorphic ``/customers/`` collection.

    ``_href`` points at the subtype detail route, which is the only way a
    caller can fetch the full record: Simpro publishes no ``/customers/{id}``.
    The contract's example is a path, not an absolute URL, so this needs no
    request context.
    """
    subtype = "companies" if customer.type == "Company" else "individuals"
    return {
        "ID": customer.id,
        "Type": customer.type,
        "CompanyName": customer.company_name,
        "GivenName": customer.given_name,
        "FamilyName": customer.family_name,
        "_href": (
            f"/api/v1.0/companies/{customer.company_id}/customers/"
            f"{subtype}/{customer.id}"
        ),
    }


def _customer_common(customer: Customer) -> dict[str, Any]:
    """The detail fields both customer subtypes share.

    ``Banking`` and ``Rates`` are omitted by ADR-013's fidelity scope.
    ``Contracts`` and ``ResponseTimes`` are nullable upstream and the mock
    models neither, so they are ``None``. ``Tags`` and ``PreferredTechs`` are
    required arrays, and an empty one is legal.
    """
    return {
        "ID": customer.id,
        "Type": customer.type,
        "Email": customer.email,
        "Phone": customer.phone,
        "AltPhone": customer.alt_phone,
        "Address": _address(customer),
        "BillingAddress": {
            "Address": customer.billing_address,
            "City": customer.billing_city,
            "State": customer.billing_state,
            "PostalCode": customer.billing_postal_code,
            "Country": customer.billing_country,
        },
        "CustomerType": customer.customer_type,
        "DoNotCall": customer.do_not_call,
        "Archived": customer.archived,
        "AmountOwing": float(customer.amount_owing),
        "Profile": {
            "Notes": customer.profile_notes,
            "Currency": {
                "ID": customer.currency_code,
                "Name": customer.currency_name,
                "Visible": True,
            },
            "AccountManager": None,
            "CustomerGroup": None,
            "CustomerProfile": None,
            "ServiceJobCostCenter": None,
        },
        "Sites": [{"ID": site.id, "Name": site.name} for site in customer.sites],
        "Tags": [],
        "PreferredTechs": [],
        "Contacts": [
            {
                "ID": contact.id,
                "GivenName": contact.given_name,
                "FamilyName": contact.family_name,
                "Email": contact.email,
                "InvoiceContact": contact.invoice_contact,
                "PrimaryInvoiceContact": contact.primary_invoice_contact,
                "StatementContact": contact.statement_contact,
                "PrimaryStatementContact": contact.primary_statement_contact,
            }
            for contact in customer.contacts
        ],
        "Contracts": None,
        "ResponseTimes": None,
        "CustomFields": [],
        "DateCreated": customer.date_created.isoformat(),
        "DateModified": customer.date_modified.isoformat(),
    }


def individual_customer_list_dict(customer: Customer) -> dict[str, Any]:
    """The fields Simpro's individual-customer collection route returns."""
    return {
        "ID": customer.id,
        "Type": customer.type,
        "GivenName": customer.given_name,
        "FamilyName": customer.family_name,
    }


def individual_customer_detail_dict(customer: Customer) -> dict[str, Any]:
    """An individual customer's documented detail fields."""
    return _customer_common(customer) | {
        "GivenName": customer.given_name,
        "FamilyName": customer.family_name,
        "Title": customer.title,
        "CellPhone": customer.cell_phone,
    }


def company_customer_list_dict(customer: Customer) -> dict[str, Any]:
    """The fields Simpro's company-customer collection route returns."""
    return {
        "ID": customer.id,
        "Type": customer.type,
        "CompanyName": customer.company_name,
    }


def company_customer_detail_dict(customer: Customer) -> dict[str, Any]:
    """A company customer's documented detail fields."""
    return _customer_common(customer) | {
        "CompanyName": customer.company_name,
        "CompanyNumber": customer.company_number,
        "EIN": customer.ein,
        "Fax": customer.fax,
        "Website": customer.website,
    }


# ----------------------------------------------------------------- contacts


def contact_list_dict(contact: Contact) -> dict[str, Any]:
    """The three fields Simpro's contact collection route returns."""
    return {
        "ID": contact.id,
        "GivenName": contact.given_name,
        "FamilyName": contact.family_name,
    }


def contact_detail_dict(contact: Contact) -> dict[str, Any]:
    """A contact's documented detail fields, including the eight role flags.

    ``Contact`` is a nullable self-reference the mock does not model.
    """
    return {
        "ID": contact.id,
        "GivenName": contact.given_name,
        "FamilyName": contact.family_name,
        "Title": contact.title,
        "Position": contact.position,
        "Department": contact.department,
        "Email": contact.email,
        "WorkPhone": contact.work_phone,
        "CellPhone": contact.cell_phone,
        "AltPhone": contact.alt_phone,
        "Fax": contact.fax,
        "Notes": contact.notes,
        "JobContact": contact.job_contact,
        "PrimaryJobContact": contact.primary_job_contact,
        "QuoteContact": contact.quote_contact,
        "PrimaryQuoteContact": contact.primary_quote_contact,
        "InvoiceContact": contact.invoice_contact,
        "PrimaryInvoiceContact": contact.primary_invoice_contact,
        "StatementContact": contact.statement_contact,
        "PrimaryStatementContact": contact.primary_statement_contact,
        "Contact": None,
        "CustomFields": [],
        "DateModified": contact.date_modified.isoformat(),
    }


# -------------------------------------------------------------------- sites


def site_list_dict(site: Site) -> dict[str, Any]:
    """The two fields Simpro's site collection route returns."""
    return {"ID": site.id, "Name": site.name}


def site_detail_dict(site: Site) -> dict[str, Any]:
    """A site's documented detail fields.

    ``BillingAddress`` has no ``Country`` member upstream — it is the one
    address shape in the contract that does not. ``Rates`` is out of ADR-013's
    fidelity scope. ``PreferredTechs`` and ``PreferredTechnicians`` are
    required arrays the mock has no data for, and empty ones are legal.
    """
    contact = site.primary_contact
    return {
        "ID": site.id,
        "Name": site.name,
        "Address": _address(site),
        "BillingAddress": {
            "Address": site.billing_address,
            "City": site.billing_city,
            "State": site.billing_state,
            "PostalCode": site.billing_postal_code,
        },
        "BillingContact": site.billing_contact,
        "Customers": [_customer_ref(customer) for customer in site.customers],
        "PrimaryContact": {
            "GivenName": contact.given_name if contact else "",
            "FamilyName": contact.family_name if contact else "",
            "Title": contact.title if contact else "",
            "Position": contact.position if contact else "",
            "Email": contact.email if contact else "",
            "WorkPhone": contact.work_phone if contact else "",
            "CellPhone": contact.cell_phone if contact else "",
            "Fax": contact.fax if contact else "",
            "PreferredNotificationMethod": "Email",
            "Contact": None,
        },
        "PublicNotes": site.public_notes,
        "PrivateNotes": site.private_notes,
        "Zone": _named_ref(site.zone),
        "STCZone": None,
        "VEECZone": None,
        "PreferredTechs": [],
        "PreferredTechnicians": [],
        "CustomFields": _custom_fields(site.custom_field_values),
        "Archived": site.archived,
        "DateModified": site.date_modified.isoformat(),
    }
