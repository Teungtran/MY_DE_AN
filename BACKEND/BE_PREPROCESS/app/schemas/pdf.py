from typing import Dict, List, Optional,Literal, Annotated

from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict
from typing import Annotated, List,Literal
from schemas.document_metadata import DocumentMetadata

class PDFRequest(BaseModel):
    pdfs: List[DocumentMetadata]


class PDFResponse(BaseModel):
    """Response body after accepting PDF for processing."""

    message: str


class WebhookRequest(BaseModel):
    """Payload sent TO the webhook URL."""

    succeeded_pdfs: List[str] = Field(..., description="List of successfully processed pdfs")
    failed_pdfs: List[str] = Field(..., description="List of pdfs that failed processing (crawler returned None)")
    error_pdfs: List[Dict[str, str]] = Field(
        ...,
        description="List of pdfs with errors during processing, including the error message [{'url': url, 'error': msg}]",
    )
    message: str = Field(..., description="Status of the S3 upload ('succeeded', 'failed')")
    trace_id: str


class WebhookResponse(BaseModel):
    """Response expected FROM the webhook endpoint (if you implement one)."""

    message: str
    trace_id: Optional[str] = None