from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class Attachment(SimproBaseModel):
    id: int = Field(alias="ID")
    job_id: int = Field(alias="JobID")
    filename: str = Field(alias="Filename")
    mime_type: str | None = Field(default=None, alias="MimeType")
    file_size: int | None = Field(default=None, alias="FileSize")
    uploaded_at: datetime | None = Field(default=None, alias="UploadedAt")
