from typing import Optional

from pydantic import BaseModel, Field


# Template model using Pydantic with descriptions added to the fields
# Template model using Pydantic with descriptions added to the fields
class Template(BaseModel):
    combined_template: str = Field(
        ...,
        description="The full combined template that defines the structure and flow.",
    )
    base_instructions: str = Field(
        ...,
        description="Basic instructions that serve as a foundation for the template's execution.",
    )
    user_info: str = Field(
        ...,
        description="Information about the user that will be incorporated into the template.",
    )
    current_time: str = Field(
        ...,
        description="Current local time zone that will be incorporated into the template.",
    )
    conversation_summary: Optional[str] = Field(None, description="Summary of the ongoing conversation, if available.")
    formatting_instructions: str = Field(
        ...,
        description="Instructions for how the output should be formatted (e.g., JSON, text).",
    )
    multi_query: Optional[str] = Field(
        None,
        description="Instructions or rules for handling multi-query situations (optional).",
    )

    class Config:
        # Forbid any extra fields that are not explicitly defined in the model
        extra = "forbid"
