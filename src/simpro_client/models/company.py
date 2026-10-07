from datetime import datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import CompanyAddress, NamedRef


class Company(SimproBaseModel):
    """A Simpro company (a "build" may hold several).

    The collection route returns only ``ID`` and ``Name``; every other field
    below comes from the detail route and is therefore optional. Requiring any
    of them would reject a valid list payload.

    The ``Banking`` block is deliberately not modelled (ADR-013 fidelity
    scope); ``extra="ignore"`` drops it rather than rejecting it.
    """

    id: int = Field(alias="ID")
    name: str = Field(alias="Name")

    # --- Detail route only, from here down ---
    address: CompanyAddress | None = Field(default=None, alias="Address")
    billing_address: CompanyAddress | None = Field(
        default=None, alias="BillingAddress"
    )
    phone: str | None = Field(default=None, alias="Phone")
    fax: str | None = Field(default=None, alias="Fax")
    email: str | None = Field(default=None, alias="Email")
    website: str | None = Field(default=None, alias="Website")
    country: str | None = Field(default=None, alias="Country")
    currency: str | None = Field(default=None, alias="Currency")
    timezone: str | None = Field(default=None, alias="Timezone")
    timezone_offset: str | None = Field(default=None, alias="TimezoneOffset")
    company_no: str | None = Field(default=None, alias="CompanyNo")
    ein: str | None = Field(default=None, alias="EIN")
    employer_tax_ref_no: str | None = Field(default=None, alias="EmployerTaxRefNo")
    cis_cert_no: str | None = Field(default=None, alias="CISCertNo")
    licence: str | None = Field(default=None, alias="Licence")
    tax_name: str | None = Field(default=None, alias="TaxName")
    default_language: str | None = Field(default=None, alias="DefaultLanguage")
    default_cost_center: NamedRef | None = Field(
        default=None, alias="DefaultCostCenter"
    )
    single_cost_center_mode: bool | None = Field(
        default=None, alias="SingleCostCenterMode"
    )
    simpro_payments: bool | None = Field(default=None, alias="SimproPayments")
    template: bool | None = Field(default=None, alias="Template")
    multi_company_label: str | None = Field(default=None, alias="MultiCompanyLabel")
    multi_company_color: str | None = Field(default=None, alias="MultiCompanyColor")
    schedule_format: int | None = Field(default=None, alias="ScheduleFormat")
    ui_date_format: str | None = Field(default=None, alias="UIDateFormat")
    ui_time_format: str | None = Field(default=None, alias="UITimeFormat")
    date_modified: datetime | None = Field(default=None, alias="DateModified")
