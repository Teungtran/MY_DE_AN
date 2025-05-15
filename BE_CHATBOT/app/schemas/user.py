from typing import List, Optional

from pydantic import BaseModel, Field


# UserProfile class using Pydantic with descriptions added to the fields
class UserProfile(BaseModel):
    username: str = Field(..., description="The unique username chosen by the user.")
    email: str = Field(..., description="The email address associated with the user.")
    company: Optional[str] = Field(None, description="The company the user works for, if available.")
    department: Optional[str] = Field(None, description="The department where the user works, if provided.")
    country: Optional[str] = Field(None, description="The country where the user resides.")
    plugins: List[str] = Field(
        ...,
        description="List of plugin names or identifiers that the user can access or has installed.",
    )
    roles: Optional[List[str]] = Field(
        None,
        description="A list of roles the user has within the system (e.g., admin, user).",
    )
