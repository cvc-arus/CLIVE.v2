from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Site(SimproBaseModel):
    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    customer_id: int = Field(alias="CustomerID")
    name: str = Field(alias="Name")
    address: str | None = Field(default=None, alias="Address")
    city: str | None = Field(default=None, alias="City")
    postcode: str | None = Field(default=None, alias="Postcode")
    state: str | None = Field(default=None, alias="State")
    country: str | None = Field(default=None, alias="Country")
