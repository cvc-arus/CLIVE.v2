from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import NamedRef, StaffRef


class Attachment(SimproBaseModel):
    """A file attached to a job.

    ``ID`` is a **string** upstream, not an integer, so
    ``ResourceEndpoint.get`` accepts ``int | str``.

    The collection route returns only ``ID`` and ``Filename``; everything else
    comes from the detail route and is therefore optional here. There is no
    ``JobID``: the job is already in the request path.
    """

    id: str = Field(alias="ID")
    filename: str = Field(alias="Filename")
    mime_type: str | None = Field(default=None, alias="MimeType")
    file_size_bytes: int | None = Field(default=None, alias="FileSizeBytes")
    date_added: datetime | None = Field(default=None, alias="DateAdded")
    public: bool | None = Field(default=None, alias="Public")
    email: bool | None = Field(default=None, alias="Email")
    folder: NamedRef | None = Field(default=None, alias="Folder")
    added_by: StaffRef | None = Field(default=None, alias="AddedBy")
