from datetime import date, datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import (
    ContactRef,
    ContractRef,
    CustomerRef,
    CustomFieldValue,
    Money,
    NamedRef,
    StaffRef,
    StatusRef,
    StcDetails,
)


class Quote(SimproBaseModel):
    """A Simpro quote.

    Like :class:`~simpro_client.models.job.Job`, only ``ID``, ``Description``
    and ``Total`` are required, because the collection route returns exactly
    those three. ``Total`` is a nested object, not a number, and there is no
    ``CustomerID`` — ``Customer`` is an object.

    ``Stage`` differs from a job's: a quote is ``InProgress``, ``Complete`` or
    ``Approved``.

    The ``Totals`` and ``Forecast`` analytic blocks are out of ADR-013's
    fidelity scope and are not modelled.
    """

    id: int = Field(alias="ID")
    description: str = Field(alias="Description")
    total: Money = Field(alias="Total")

    # --- Detail route only, from here down ---
    name: str | None = Field(default=None, alias="Name")
    type: str | None = Field(default=None, alias="Type")
    stage: str | None = Field(default=None, alias="Stage")
    customer_stage: str | None = Field(default=None, alias="CustomerStage")
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
    additional_customers: list[CustomerRef] | None = Field(
        default=None, alias="AdditionalCustomers"
    )
    tags: list[NamedRef] | None = Field(default=None, alias="Tags")
    notes: str | None = Field(default=None, alias="Notes")
    order_no: str | None = Field(default=None, alias="OrderNo")
    request_no: str | None = Field(default=None, alias="RequestNo")
    job_no: str | None = Field(default=None, alias="JobNo")
    linked_job_id: int | None = Field(default=None, alias="LinkedJobID")
    date_issued: date | None = Field(default=None, alias="DateIssued")
    date_approved: date | None = Field(default=None, alias="DateApproved")
    due_date: date | None = Field(default=None, alias="DueDate")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
    validity_days: int | None = Field(default=None, alias="ValidityDays")
    auto_adjust_status: bool | None = Field(default=None, alias="AutoAdjustStatus")
    is_variation: bool | None = Field(default=None, alias="IsVariation")
    is_closed: bool | None = Field(default=None, alias="IsClosed")
    converted_from_lead: NamedRef | None = Field(
        default=None, alias="ConvertedFromLead"
    )
    archive_reason: NamedRef | None = Field(default=None, alias="ArchiveReason")
    stc: StcDetails | None = Field(default=None, alias="STC")
    custom_fields: list[CustomFieldValue] | None = Field(
        default=None, alias="CustomFields"
    )
