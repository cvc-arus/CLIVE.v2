from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Company(SimproBaseModel):
    """Simpro company model"""

    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
