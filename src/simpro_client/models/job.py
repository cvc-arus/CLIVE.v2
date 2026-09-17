from datetime import date

from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Job(SimproBaseModel):
    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    name: str = Field(alias="Name")
    status: str = Field(alias="Status")
    date_issued: date | None = Field(default=None, alias="DateIssued")
    total: float = Field(alias="Total")
