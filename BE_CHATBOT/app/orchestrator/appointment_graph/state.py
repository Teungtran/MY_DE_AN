from pydantic import BaseModel, Field
class ToAppointmentAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle electronics products recommendations, orders and cancellations."""

    request: str = Field(
        description="Any necessary followup questions the tech assistant should clarify before proceeding."
    )
