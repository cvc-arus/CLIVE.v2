from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import AddressBlock, EmployeeContact, NamedRef


class Employee(SimproBaseModel):
    """A Simpro employee.

    Upstream an employee has a single ``Name``, not ``GivenName`` /
    ``FamilyName``, and contact details are nested under ``PrimaryContact``
    rather than flat ``Email`` / ``Phone`` fields.

    Only ``ID`` and ``Name`` are required, because the collection route returns
    just those two. There is no ``CompanyID``: the company is in the path.

    The ``Banking`` and ``PayRates`` blocks are deliberately not modelled
    (ADR-013 fidelity scope). ``extra="ignore"`` means they are dropped rather
    than rejected, and adding them later is not a breaking change.
    """

    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    position: str | None = Field(default=None, alias="Position")
    primary_contact: EmployeeContact | None = Field(
        default=None, alias="PrimaryContact"
    )
    address: AddressBlock | None = Field(default=None, alias="Address")
    zones: list[NamedRef] | None = Field(default=None, alias="Zones")
    default_zone: NamedRef | None = Field(default=None, alias="DefaultZone")
    default_company: NamedRef | None = Field(default=None, alias="DefaultCompany")
    archived: bool | None = Field(default=None, alias="Archived")
    date_created: datetime | None = Field(default=None, alias="DateCreated")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
