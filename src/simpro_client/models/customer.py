"""Simpro customers, which are polymorphic.

Upstream a customer is either an individual or a company, and the two have
different name fields and different detail routes. There are three shapes, not
one (ADR-013 decision 2):

``CustomerSummary``
    What ``/customers/`` returns: a thin row carrying the ``Type``
    discriminator and an ``_href`` pointing at the subtype's detail route.
``IndividualCustomer`` / ``CompanyCustomer``
    The full records, from ``/customers/individuals/{id}`` and
    ``/customers/companies/{id}``.

``_CustomerBase`` holds what the two subtypes share. It is private: callers
should name the concrete subtype, and nothing is exported from it.

``Banking`` and ``Rates`` are out of ADR-013's fidelity scope, so they are not
modelled. ``extra="ignore"`` drops them rather than rejecting them.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import (
    AddressBlock,
    ContractRef,
    CustomerContactRef,
    CustomerProfile,
    NamedRef,
    StaffRef,
)


class CustomerSummary(SimproBaseModel):
    """A row from the polymorphic ``/customers/`` collection.

    Every field is required: this shape appears on one route only, so there is
    no narrower leg to accommodate. ``Type`` and ``href`` are what tell a
    caller which subtype endpoint to follow.
    """

    id: int = Field(alias="ID")
    type: str = Field(alias="Type")
    company_name: str = Field(alias="CompanyName")
    given_name: str = Field(alias="GivenName")
    family_name: str = Field(alias="FamilyName")
    href: str = Field(alias="_href")


class _CustomerBase(SimproBaseModel):
    """Fields common to both customer subtypes.

    Only ``ID`` and ``Type`` are required, because they are the only two the
    contract marks required on both the subtype's list and detail responses.
    """

    id: int = Field(alias="ID")
    type: str = Field(alias="Type")
    email: str | None = Field(default=None, alias="Email")
    phone: str | None = Field(default=None, alias="Phone")
    alt_phone: str | None = Field(default=None, alias="AltPhone")
    address: AddressBlock | None = Field(default=None, alias="Address")
    billing_address: AddressBlock | None = Field(default=None, alias="BillingAddress")
    customer_type: str | None = Field(default=None, alias="CustomerType")
    do_not_call: bool | None = Field(default=None, alias="DoNotCall")
    archived: bool | None = Field(default=None, alias="Archived")
    amount_owing: Decimal | None = Field(default=None, alias="AmountOwing")
    profile: CustomerProfile | None = Field(default=None, alias="Profile")
    sites: list[NamedRef] | None = Field(default=None, alias="Sites")
    tags: list[NamedRef] | None = Field(default=None, alias="Tags")
    preferred_techs: list[StaffRef] | None = Field(default=None, alias="PreferredTechs")
    contacts: list[CustomerContactRef] | None = Field(default=None, alias="Contacts")
    contracts: list[ContractRef] | None = Field(default=None, alias="Contracts")
    response_times: list[NamedRef] | None = Field(default=None, alias="ResponseTimes")
    date_created: datetime | None = Field(default=None, alias="DateCreated")
    date_modified: datetime | None = Field(default=None, alias="DateModified")


class IndividualCustomer(_CustomerBase):
    """A customer who is a person.

    ``GivenName`` and ``FamilyName`` are required: the contract marks them
    required on both the individuals list and the individuals detail response.
    """

    given_name: str = Field(alias="GivenName")
    family_name: str = Field(alias="FamilyName")
    title: str | None = Field(default=None, alias="Title")
    cell_phone: str | None = Field(default=None, alias="CellPhone")


class CompanyCustomer(_CustomerBase):
    """A customer that is an organisation.

    ``CompanyName`` is required: the contract marks it required on both the
    companies list and the companies detail response.
    """

    company_name: str = Field(alias="CompanyName")
    company_number: str | None = Field(default=None, alias="CompanyNumber")
    ein: str | None = Field(default=None, alias="EIN")
    fax: str | None = Field(default=None, alias="Fax")
    website: str | None = Field(default=None, alias="Website")


__all__ = [
    "CompanyCustomer",
    "CustomerSummary",
    "IndividualCustomer",
]
