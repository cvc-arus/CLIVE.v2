from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Project(SimproBaseModel):
    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    customer_id: int = Field(alias="CustomerID")
    site_id: int | None = Field(default=None, alias="SiteID")
    name: str = Field(alias="Name")
    status: str = Field(alias="Status")
    total: float = Field(alias="Total")
