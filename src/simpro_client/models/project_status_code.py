from pydantic import Field

from simpro_client.models.base import SimproBaseModel


class ProjectStatusCode(SimproBaseModel):
    """A Simpro project status code.

    Job and quote statuses draw their IDs from this list: the spec documents the
    ``Status`` field of the Job POST, Job PATCH and Quote POST bodies as
    "ID of a project status code" (ADR-013 §7).

    The field set still reflects the mock's invented shape. It is re-shaped to
    the published contract in ADR-013's Wave A, which drops ``CompanyID``,
    ``Category`` and ``IsDefault`` and adds ``Color``, ``Priority`` and
    ``DateModified``.
    """

    id: int = Field(alias="ID")
    company_id: int = Field(alias="CompanyID")
    name: str = Field(alias="Name")
    category: str | None = Field(default=None, alias="Category")
    is_default: bool = Field(alias="IsDefault")
