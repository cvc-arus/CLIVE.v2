"""Nested value objects shared by Simpro resource models.

Simpro returns composite values as nested objects rather than flat fields: a
staff member is ``{"ID", "Name", "Type", "TypeId"}``, not a bare integer id.
The objects here are the reusable pieces of that shape, as documented in
``docs/contracts/simpro-openapi-v1-get-subset.json`` (ADR-013).

They are added as they are first consumed, not all at once, so every class here
is reachable from a resource model and covered by
``tests/test_spec_conformance.py``.

Optionality follows the contract. Where the spec marks an inner field required,
it is required here; where the containing object is itself nullable or
optional, the *owning* model declares it optional, not these classes.
"""

from datetime import date

from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class NamedRef(SimproBaseModel):
    """An ``{"ID", "Name"}`` reference to another record.

    Both fields are optional because the spec uses this shape in two ways: as
    a required reference with both members required (``Employee.DefaultZone``),
    and as a nullable lookup whose members are themselves optional
    (``Attachment.Folder``, ``Company.DefaultCostCenter``). Optional here
    accepts both, and the owning model carries the nullability.
    """

    id: int | None = Field(default=None, alias="ID")
    name: str | None = Field(default=None, alias="Name")


class StaffRef(SimproBaseModel):
    """A reference to a person who can be assigned work.

    ``Type`` distinguishes the three staff kinds Simpro models separately, and
    ``TypeId`` is the record's id within that kind.
    """

    id: int | None = Field(default=None, alias="ID")
    name: str | None = Field(default=None, alias="Name")
    type: str | None = Field(default=None, alias="Type")
    type_id: int | None = Field(default=None, alias="TypeId")


class CompanyAddress(SimproBaseModel):
    """A company's two-line address.

    Distinct from :class:`AddressBlock`: the company endpoints document an
    address as two free-text lines, while sites and employees use discrete
    city/state/postcode fields.
    """

    line1: str = Field(alias="Line1")
    line2: str = Field(alias="Line2")


class AddressBlock(SimproBaseModel):
    """A structured postal address, as used by employees and sites."""

    address: str = Field(alias="Address")
    city: str = Field(alias="City")
    state: str = Field(alias="State")
    postal_code: str = Field(alias="PostalCode")
    country: str = Field(alias="Country")


class EmployeeContact(SimproBaseModel):
    """An employee's ``PrimaryContact`` block."""

    email: str = Field(alias="Email")
    secondary_email: str = Field(alias="SecondaryEmail")
    work_phone: str = Field(alias="WorkPhone")
    cell_phone: str = Field(alias="CellPhone")
    extension: str = Field(alias="Extension")
    fax: str = Field(alias="Fax")
    preferred_notification_method: str | None = Field(
        default=None, alias="PreferredNotificationMethod"
    )


class NoteVisibility(SimproBaseModel):
    """Who may see a job note. Both audiences are required by the spec."""

    admin: bool = Field(alias="Admin")
    customer: bool = Field(alias="Customer")


class NoteReference(SimproBaseModel):
    """What a job note refers to.

    ``Text`` is the only required member; ``Number`` and ``Type`` are nullable
    and absent when the note is not tied to a numbered record.
    """

    text: str = Field(alias="Text")
    number: str | None = Field(default=None, alias="Number")
    type: str | None = Field(default=None, alias="Type")


class NoteAttachment(SimproBaseModel):
    """A file attached to a job note.

    ``href`` is aliased from ``_href``. A Pydantic field *named* ``_href``
    silently becomes a private attribute and disappears from the model, so the
    leading underscore must live only in the alias.
    """

    file_name: str = Field(alias="FileName")
    href: str = Field(alias="_href")


class SiteBillingAddress(SimproBaseModel):
    """A site's billing address.

    Deliberately **not** :class:`AddressBlock`: the site billing address is the
    one address shape in the contract with no ``Country`` member.
    """

    address: str = Field(alias="Address")
    city: str = Field(alias="City")
    state: str = Field(alias="State")
    postal_code: str = Field(alias="PostalCode")


class ContactRef(SimproBaseModel):
    """A nullable pointer at a contact record, by name and id."""

    id: int | None = Field(default=None, alias="ID")
    given_name: str | None = Field(default=None, alias="GivenName")
    family_name: str | None = Field(default=None, alias="FamilyName")
    email: str | None = Field(default=None, alias="Email")


class CustomerRef(SimproBaseModel):
    """A customer as it appears inside another resource.

    Carries both name shapes because the discriminator decides which is
    meaningful: ``CompanyName`` for a company, ``GivenName``/``FamilyName`` for
    an individual. Unlike the customers collection, this shape has no
    ``_href``.
    """

    id: int | None = Field(default=None, alias="ID")
    type: str | None = Field(default=None, alias="Type")
    company_name: str | None = Field(default=None, alias="CompanyName")
    given_name: str | None = Field(default=None, alias="GivenName")
    family_name: str | None = Field(default=None, alias="FamilyName")


class CustomerContactRef(SimproBaseModel):
    """A contact listed on a customer, with its invoicing roles."""

    id: int | None = Field(default=None, alias="ID")
    given_name: str | None = Field(default=None, alias="GivenName")
    family_name: str | None = Field(default=None, alias="FamilyName")
    email: str | None = Field(default=None, alias="Email")
    invoice_contact: bool | None = Field(default=None, alias="InvoiceContact")
    primary_invoice_contact: bool | None = Field(
        default=None, alias="PrimaryInvoiceContact"
    )
    statement_contact: bool | None = Field(default=None, alias="StatementContact")
    primary_statement_contact: bool | None = Field(
        default=None, alias="PrimaryStatementContact"
    )


class ContractRef(SimproBaseModel):
    """A customer contract. Both dates are nullable upstream."""

    id: int | None = Field(default=None, alias="ID")
    name: str | None = Field(default=None, alias="Name")
    contract_no: str | None = Field(default=None, alias="ContractNo")
    start_date: date | None = Field(default=None, alias="StartDate")
    end_date: date | None = Field(default=None, alias="EndDate")
    expired: bool | None = Field(default=None, alias="Expired")


class Currency(SimproBaseModel):
    """A currency. Note ``ID`` is a *string* here, not an integer."""

    id: str | None = Field(default=None, alias="ID")
    name: str | None = Field(default=None, alias="Name")
    visible: bool | None = Field(default=None, alias="Visible")


class CustomerProfile(SimproBaseModel):
    """A customer's ``Profile`` block: grouping, ownership and free notes."""

    notes: str | None = Field(default=None, alias="Notes")
    currency: Currency | None = Field(default=None, alias="Currency")
    account_manager: NamedRef | None = Field(default=None, alias="AccountManager")
    customer_group: NamedRef | None = Field(default=None, alias="CustomerGroup")
    customer_profile: NamedRef | None = Field(default=None, alias="CustomerProfile")
    service_job_cost_center: NamedRef | None = Field(
        default=None, alias="ServiceJobCostCenter"
    )


class SitePrimaryContact(SimproBaseModel):
    """A site's primary contact.

    A different shape from :class:`EmployeeContact`: a site's contact is a
    named person with a position, not a bundle of phone numbers.
    """

    given_name: str | None = Field(default=None, alias="GivenName")
    family_name: str | None = Field(default=None, alias="FamilyName")
    title: str | None = Field(default=None, alias="Title")
    position: str | None = Field(default=None, alias="Position")
    email: str | None = Field(default=None, alias="Email")
    work_phone: str | None = Field(default=None, alias="WorkPhone")
    cell_phone: str | None = Field(default=None, alias="CellPhone")
    fax: str | None = Field(default=None, alias="Fax")
    preferred_notification_method: str | None = Field(
        default=None, alias="PreferredNotificationMethod"
    )
    contact: ContactRef | None = Field(default=None, alias="Contact")


class PreferredTechnician(SimproBaseModel):
    """A site's preferred technician, optionally scoped to an asset type."""

    staff: StaffRef | None = Field(default=None, alias="Staff")
    asset_type: NamedRef | None = Field(default=None, alias="AssetType")
    service_level: NamedRef | None = Field(default=None, alias="ServiceLevel")


class CustomFieldDefinition(SimproBaseModel):
    """The definition half of a custom field: its name, type and options."""

    id: int | None = Field(default=None, alias="ID")
    name: str | None = Field(default=None, alias="Name")
    type: str | None = Field(default=None, alias="Type")
    is_mandatory: bool | None = Field(default=None, alias="IsMandatory")
    list_items: list[str] | None = Field(default=None, alias="ListItems")


class CustomFieldValue(SimproBaseModel):
    """One custom field and its value on a record.

    Simpro keeps asset serial numbers, models and manufacturers here, which is
    why ``CustomFields`` is in ADR-013's fidelity scope at all.
    """

    custom_field: CustomFieldDefinition | None = Field(
        default=None, alias="CustomField"
    )
    value: str | None = Field(default=None, alias="Value")


__all__ = [
    "AddressBlock",
    "CompanyAddress",
    "ContactRef",
    "ContractRef",
    "Currency",
    "CustomFieldDefinition",
    "CustomFieldValue",
    "CustomerContactRef",
    "CustomerProfile",
    "CustomerRef",
    "EmployeeContact",
    "NamedRef",
    "NoteAttachment",
    "NoteReference",
    "NoteVisibility",
    "PreferredTechnician",
    "SiteBillingAddress",
    "SitePrimaryContact",
    "StaffRef",
]
