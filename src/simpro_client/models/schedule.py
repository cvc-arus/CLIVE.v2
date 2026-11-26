from datetime import date as date_type
from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import StaffRef


class Schedule(SimproBaseModel):
    """A company-level schedule entry (``/companies/{id}/schedules/``).

    ``Type`` is one of ``lead``, ``quote``, ``job`` or ``activity``. For job
    and quote schedules ``Reference`` is the job or quote ID and the cost
    centre ID joined by a hyphen (``"123-45"``); for activities it is the
    activity type ID and for leads the lead ID.

    The contract marks more fields required on the list route (``TotalHours``,
    ``Staff``, ``Blocks``, ``Project``), but only ``ID``, ``Type`` and
    ``Reference`` are required here so that a ``columns`` projection stays
    small (ADR-016). ``Blocks`` is not modelled; ``extra="ignore"`` drops it.

    ``date`` is imported as ``date_type`` because the ``date`` field would
    otherwise shadow the type (``src/simpro_client/CLAUDE.md`` §7).
    """

    id: int = Field(alias="ID")
    type: str = Field(alias="Type")
    reference: str = Field(alias="Reference")
    date: date_type | None = Field(default=None, alias="Date")
    total_hours: float | None = Field(default=None, alias="TotalHours")
    staff: StaffRef | None = Field(default=None, alias="Staff")
    project: str | None = Field(default=None, alias="Project")
    # --- Detail route only, from here down ---
    notes: str | None = Field(default=None, alias="Notes")
    is_locked: bool | None = Field(default=None, alias="IsLocked")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
