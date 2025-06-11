from pydantic import BaseModel, Field
from typing_extensions import Optional

class ToITAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle FPT policy-related questions."""

    request: str = Field(
        description="Any necessary followup questions the policy assistant should clarify before proceeding."
    )
