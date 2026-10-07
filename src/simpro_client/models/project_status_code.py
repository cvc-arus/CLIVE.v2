from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class ProjectStatusCode(SimproBaseModel):
    """A Simpro project status code.

    Job and quote statuses draw their IDs from this list: the spec documents the
    ``Status`` field of the Job POST, Job PATCH and Quote POST bodies as
    "ID of a project status code" (ADR-013 §7).

    Only ``ID`` and ``Name`` are required, because they are the only fields the
    contract marks required on *both* the list and the detail response. The
    rest appear on the detail route only, so requiring them here would reject a
    valid list payload.
    """

    id: int = Field(alias="ID")
    name: str = Field(alias="Name")
    color: str | None = Field(default=None, alias="Color")
    priority: int | None = Field(default=None, alias="Priority")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
