from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class JobNote(SimproBaseModel):
    id: int = Field(alias="ID")
    job_id: int = Field(alias="JobID")
    subject: str | None = Field(default=None, alias="Subject")
    note: str | None = Field(default=None, alias="Note")
    created_by: int | None = Field(default=None, alias="CreatedBy")
    created_at: datetime | None = Field(default=None, alias="CreatedAt")
