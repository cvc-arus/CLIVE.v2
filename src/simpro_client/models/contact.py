from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import ContactRef, CustomFieldValue


class Contact(SimproBaseModel):
    """A contact person at a customer.

    Only ``ID``, ``GivenName`` and ``FamilyName`` are required: the collection
    route returns just those three, and requiring anything else would reject a
    valid list payload. There is no ``CompanyID`` or ``CustomerID`` — both are
    already in the request path.

    Upstream there is no single ``Phone`` field; a contact has separate work,
    cell, alternate and fax numbers.
    """

    id: int = Field(alias="ID")
    given_name: str = Field(alias="GivenName")
    family_name: str = Field(alias="FamilyName")
    title: str | None = Field(default=None, alias="Title")
    position: str | None = Field(default=None, alias="Position")
    department: str | None = Field(default=None, alias="Department")
    email: str | None = Field(default=None, alias="Email")
    work_phone: str | None = Field(default=None, alias="WorkPhone")
    cell_phone: str | None = Field(default=None, alias="CellPhone")
    alt_phone: str | None = Field(default=None, alias="AltPhone")
    fax: str | None = Field(default=None, alias="Fax")
    notes: str | None = Field(default=None, alias="Notes")

    # The eight contact-role flags. Simpro tracks "is a job contact" and "is
    # *the* job contact" separately, for each of the four record types.
    job_contact: bool | None = Field(default=None, alias="JobContact")
    primary_job_contact: bool | None = Field(default=None, alias="PrimaryJobContact")
    quote_contact: bool | None = Field(default=None, alias="QuoteContact")
    primary_quote_contact: bool | None = Field(
        default=None, alias="PrimaryQuoteContact"
    )
    invoice_contact: bool | None = Field(default=None, alias="InvoiceContact")
    primary_invoice_contact: bool | None = Field(
        default=None, alias="PrimaryInvoiceContact"
    )
    statement_contact: bool | None = Field(default=None, alias="StatementContact")
    primary_statement_contact: bool | None = Field(
        default=None, alias="PrimaryStatementContact"
    )

    contact: ContactRef | None = Field(default=None, alias="Contact")
    custom_fields: list[CustomFieldValue] | None = Field(
        default=None, alias="CustomFields"
    )
    date_modified: datetime | None = Field(default=None, alias="DateModified")
