from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Employee(SimproBaseModel):
    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    given_name: str = Field(alias="GivenName")
    family_name: str = Field(alias="FamilyName")
    position: str | None = Field(default=None, alias="Position")
    email: str | None = Field(default=None, alias="Email")
    phone: str | None = Field(default=None, alias="Phone")
