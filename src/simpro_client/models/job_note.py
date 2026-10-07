from datetime import date, datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import (
    NoteAttachment,
    NoteReference,
    NoteVisibility,
    StaffRef,
)


class JobNote(SimproBaseModel):
    """A note recorded against a job.

    ``Reference`` and ``Visibility`` are required because the contract marks
    them required on both the list and the detail response. ``Subject`` is
    required but nullable on the list route and merely optional on the detail
    route, so it is optional here.

    There is no ``JobID``: the job is already in the request path.
    """

    id: int = Field(alias="ID")
    reference: NoteReference = Field(alias="Reference")
    visibility: NoteVisibility = Field(alias="Visibility")
    subject: str | None = Field(default=None, alias="Subject")
    note: str | None = Field(default=None, alias="Note")
    date_created: datetime | None = Field(default=None, alias="DateCreated")
    follow_up_date: date | None = Field(default=None, alias="FollowUpDate")
    attachments: list[NoteAttachment] | None = Field(default=None, alias="Attachments")
    submitted_by: StaffRef | None = Field(default=None, alias="SubmittedBy")
    assign_to: StaffRef | None = Field(default=None, alias="AssignTo")
