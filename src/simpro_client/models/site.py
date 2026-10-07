from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import (
    AddressBlock,
    CustomerRef,
    CustomFieldValue,
    NamedRef,
    PreferredTechnician,
    SiteBillingAddress,
    SitePrimaryContact,
    StaffRef,
)


class Site(SimproBaseModel):
    """A customer site.

    Only ``ID`` and ``Name`` are required: the collection route returns just
    those two. There is no ``CompanyID``, and no single ``CustomerID`` — a site
    can belong to several customers, so the contract gives it a ``Customers``
    array.

    The address is a nested object, not five flat fields. ``BillingAddress``
    uses :class:`SiteBillingAddress` rather than :class:`AddressBlock` because
    it is the one address shape in the contract with no ``Country``.

    ``Rates`` is out of ADR-013's fidelity scope and is not modelled.
    """

    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    address: AddressBlock | None = Field(default=None, alias="Address")
    billing_address: SiteBillingAddress | None = Field(
        default=None, alias="BillingAddress"
    )
    billing_contact: str | None = Field(default=None, alias="BillingContact")
    customers: list[CustomerRef] | None = Field(default=None, alias="Customers")
    primary_contact: SitePrimaryContact | None = Field(
        default=None, alias="PrimaryContact"
    )
    public_notes: str | None = Field(default=None, alias="PublicNotes")
    private_notes: str | None = Field(default=None, alias="PrivateNotes")
    zone: NamedRef | None = Field(default=None, alias="Zone")
    stc_zone: int | None = Field(default=None, alias="STCZone")
    veec_zone: str | None = Field(default=None, alias="VEECZone")
    preferred_techs: list[StaffRef] | None = Field(default=None, alias="PreferredTechs")
    preferred_technicians: list[PreferredTechnician] | None = Field(
        default=None, alias="PreferredTechnicians"
    )
    custom_fields: list[CustomFieldValue] | None = Field(
        default=None, alias="CustomFields"
    )
    archived: bool | None = Field(default=None, alias="Archived")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
