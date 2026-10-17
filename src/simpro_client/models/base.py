"""Shared configuration for typed Simpro resource"""

from datetime import date
from functools import cache
from types import UnionType
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


@cache
def _is_date_annotation(annotation: Any) -> bool:
    """Whether a field annotation is a date or timestamp, optionally nullable.

    Args:
        annotation: A field's resolved annotation, such as ``date | None``.

    Returns:
        True for ``date`` or ``datetime`` (a ``date`` subclass), alone or as a
        member of a union; False for anything else, including containers.
    """
    if isinstance(annotation, type):
        return issubclass(annotation, date)
    if get_origin(annotation) in (Union, UnionType):
        return any(_is_date_annotation(arg) for arg in get_args(annotation))
    return False


class SimproBaseModel(BaseModel):
    """Accept API aliases while exporting Python field names"""

    model_config = ConfigDict(
        extra="ignore",  # Accepts payloads containing fields the model does not declare
        validate_by_alias=True,  # Accepts committed PascalCase API keys.
        validate_by_name=True,  # Accepts Pythonic snake_case keys.
    )

    @field_validator("*", mode="before")
    @classmethod
    def _empty_date_to_none(cls, value: Any, info: ValidationInfo) -> Any:
        """Read Simpro's ``""`` for an empty date or timestamp as ``None``.

        Live Simpro sends the empty string where the published contract
        declares a nullable ``date`` (``docs/simpro/mock-vs-public-api.md``
        §6, item 17). Only date and timestamp fields are affected; an empty
        string anywhere else is kept as it is.

        Args:
            value: The raw input for one field.
            info: Pydantic's validation context, naming the field.

        Returns:
            ``None`` for ``""`` on a date or timestamp field, else ``value``.
        """
        if value != "" or info.field_name is None:
            return value
        field = cls.model_fields[info.field_name]
        return None if _is_date_annotation(field.annotation) else value
