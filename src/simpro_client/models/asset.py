from datetime import date, datetime

from pydantic import Field

from simpro_client.models.base import SimproBaseModel
from simpro_client.models.common import (
    ContractRef,
    CustomFieldValue,
    LastTest,
    NamedRef,
)


class Asset(SimproBaseModel):
    """A site asset.

    Only ``ID`` and ``AssetType`` are required: the collection route returns
    exactly those two. There is no ``CompanyID``, no ``SiteID`` (the site is
    in the path) and no ``AssetNo`` or ``Name`` — upstream an asset is
    identified by its type plus its custom fields.

    **The serial number, model and manufacturer live in ``CustomFields``**,
    not in dedicated fields. That is where Simpro keeps them, and it is why
    ``CustomFields`` is in ADR-013's fidelity scope at all: it holds CVC's
    CCTV asset data.
    """

    id: int = Field(alias="ID")
    asset_type: NamedRef = Field(alias="AssetType")

    # --- Detail route only, from here down ---
    start_date: date | None = Field(default=None, alias="StartDate")
    display_order: int | None = Field(default=None, alias="DisplayOrder")
    archived: bool | None = Field(default=None, alias="Archived")
    parent_id: int | None = Field(default=None, alias="ParentID")
    last_test: LastTest | None = Field(default=None, alias="LastTest")
    customer_contract: ContractRef | None = Field(
        default=None, alias="CustomerContract"
    )
    custom_fields: list[CustomFieldValue] | None = Field(
        default=None, alias="CustomFields"
    )
    date_modified: datetime | None = Field(default=None, alias="DateModified")
