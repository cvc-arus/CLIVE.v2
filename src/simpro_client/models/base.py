"""Shared configuration for typed Simpro resource"""

from pydantic import BaseModel, ConfigDict


class SimproBaseModel(BaseModel):
    """Accept API aliases while exporting Python field names"""

    model_config = ConfigDict(
        extra="ignore",  # Accepts payloads containing fields the model does not declare
        validate_by_alias = True,  # Accepts committed PascalCase API keys.
        validate_by_name=True,  # Accepts Pythonic snake_case keys.

    )
