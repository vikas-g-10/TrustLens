"""
Base Pydantic schema model with automatic camelCase aliases for TrustLens.
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model with automatic camelCase alias generator for frontend JSON serialization."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
