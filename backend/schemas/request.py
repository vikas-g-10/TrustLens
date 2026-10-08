from typing import Optional
from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    """Payload for text claim and/or URL investigation."""
    claim: Optional[str] = Field(
        default="",
        max_length=1000,
        description="Factual assertion to investigate"
    )
    url: Optional[str] = Field(
        default="",
        max_length=2048,
        description="Optional public URL to inspect"
    )
    is_demo: Optional[bool] = Field(
        default=False,
        description="Flag indicating if the client requested the verified demo case"
    )
