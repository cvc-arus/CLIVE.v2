from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Status(SimproBaseModel):
    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    name: str = Field(alias="Name")
    category: str | None = Field(default=None, alias="Category")
    is_default: bool = Field(alias="IsDefault")
