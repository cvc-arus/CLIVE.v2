from datetime import date, datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import (
    ContactRef,
    ContractRef,
    ConvertedFrom,
    ConvertedFromQuote,
    CustomerRef,
    CustomFieldValue,
    Money,
    NamedRef,
    StaffRef,
    StatusRef,
    StcDetails,
)


class Job(SimproBaseModel):
    """A Simpro job.

    A *project* is a job with ``Type: "Project"``. Simpro has no separate
    Projects resource, which is why ``simpro_client`` no longer has one
    either (ADR-013).

    Only ``ID``, ``Description`` and ``Total`` are required: the collection
    route returns exactly those three and nothing else — not even ``Name``.
    ``Total`` is a nested object, not a number.

    ``Status`` carries a project status code id, so a job's status and
    ``/setup/statusCodes/projects/`` share one id space.

    The ``Totals`` analytic block is out of ADR-013's fidelity scope and is
    not modelled; ``extra="ignore"`` drops it.
    """

    id: int = Field(alias="ID")
    description: str = Field(alias="Description")
    total: Money = Field(alias="Total")

    # --- Detail route only, from here down ---
    name: str | None = Field(default=None, alias="Name")
    type: str | None = Field(default=None, alias="Type")
    stage: str | None = Field(default=None, alias="Stage")
    status: StatusRef | None = Field(default=None, alias="Status")
    customer: CustomerRef | None = Field(default=None, alias="Customer")
    site: NamedRef | None = Field(default=None, alias="Site")
    customer_contract: ContractRef | None = Field(
        default=None, alias="CustomerContract"
    )
    customer_contact: ContactRef | None = Field(default=None, alias="CustomerContact")
    site_contact: ContactRef | None = Field(default=None, alias="SiteContact")
    project_manager: StaffRef | None = Field(default=None, alias="ProjectManager")
    salesperson: StaffRef | None = Field(default=None, alias="Salesperson")
    technician: StaffRef | None = Field(default=None, alias="Technician")
    technicians: list[StaffRef] | None = Field(default=None, alias="Technicians")
    additional_contacts: list[ContactRef] | None = Field(
        default=None, alias="AdditionalContacts"
    )
    tags: list[NamedRef] | None = Field(default=None, alias="Tags")
    notes: str | None = Field(default=None, alias="Notes")
    order_no: str | None = Field(default=None, alias="OrderNo")
    request_no: str | None = Field(default=None, alias="RequestNo")
    date_issued: date | None = Field(default=None, alias="DateIssued")
    due_date: date | None = Field(default=None, alias="DueDate")
    due_time: str | None = Field(default=None, alias="DueTime")
    completed_date: date | None = Field(default=None, alias="CompletedDate")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
    auto_adjust_status: bool | None = Field(default=None, alias="AutoAdjustStatus")
    is_variation: bool | None = Field(default=None, alias="IsVariation")
    is_retention_enabled: bool | None = Field(default=None, alias="IsRetentionEnabled")
    converted_from: ConvertedFrom | None = Field(default=None, alias="ConvertedFrom")
    converted_from_quote: ConvertedFromQuote | None = Field(
        default=None, alias="ConvertedFromQuote"
    )
    archive_reason: NamedRef | None = Field(default=None, alias="ArchiveReason")
    response_time: NamedRef | None = Field(default=None, alias="ResponseTime")
    stc: StcDetails | None = Field(default=None, alias="STC")
    custom_fields: list[CustomFieldValue] | None = Field(
        default=None, alias="CustomFields"
    )
