from pydantic import BaseModel, Field
class ToAppointmentAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle booking, tracking and canceling appointments, with user_id"""
    user_id: str = Field(
        description="The id of user from 'AgenticState'"
    ),
    request: str = Field(
        description="Any necessary followup questions the Appointment assistant should clarify before proceeding."
    )
