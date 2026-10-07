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


__all__ = [
    "AddressBlock",
    "CompanyAddress",
    "EmployeeContact",
    "NamedRef",
    "NoteAttachment",
    "NoteReference",
    "NoteVisibility",
    "StaffRef",
]
