from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field



class DocumentMetadata(BaseModel):
    source: Optional[str] = Field(default=None, description="File name or URL")
    type: Optional[Literal["RECOMMEND", "RAG"]] = Field(default=None, description='"RECOMMEND" or "RAG"')
    is_active: Optional[bool] = Field(default=None, description="Whether the document is active")
    update_at: Optional[datetime] = Field(default=None, description="Last updated timestamp")
    description: Optional[Literal["URL", "PDF"]] = Field(default=None, description='Either "URL" or "PDF"')