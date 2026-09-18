from datetime import date

from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Asset(SimproBaseModel):
    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    site_id: int = Field(alias="SiteID")
    asset_no: str = Field(alias="AssetNo")
    name: str = Field(alias="Name")
    serial_no: str | None = Field(default=None, alias="SerialNo")
    model: str | None = Field(default=None, alias="Model")
    manufacturer: str | None = Field(default=None, alias="Manufacturer")
    installed_date: date | None = Field(default=None, alias="InstalledDate")
