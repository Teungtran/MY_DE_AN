import datetime
import json
import os
import re
import tempfile
from typing import List

from fastapi import APIRouter, Depends, status, UploadFile, File

from config.base_config import APP_CONFIG
from schemas.document_metadata import DocumentMetadata
from schemas.pdf import PDFResponse
from services.data_pipeline.store.pdf_expert_knowledge_store_preprocessing_pipeline import PDFExpertPreprocessingPipeline
from services.storage.s3 import AsyncS3Client, get_s3_client
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.logger.logger import get_logger

logger = get_logger(__name__)
pdf_router = APIRouter(prefix="/pdf")

_BUCKET_NAME = APP_CONFIG.s3config.bucket_name
if _BUCKET_NAME is None:
    raise ValueError("BUCKET_NAME is not set in environment variables")
BUCKET_NAME: str = _BUCKET_NAME


def get_filename_from_pdf(file_path: str) -> str:
    # Extract the base filename without the extension
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    # Sanitize to make it safe for filenames
    filename_safe = re.sub(r"[^a-zA-Z0-9\-_.]", "-", name_without_ext)
    return filename_safe


async def process_pdfs(files: List[UploadFile], doc_metadata: List[DocumentMetadata], s3_client: AsyncS3Client):
    logger.info("Processing user-submitted PDFs")
    succeeded_list: List[str] = []
    failed_list: List[str] = []
    error_messages = []

    if not files:
        logger.error("No PDF files found")
        return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}
        
    if len(files) == 1:
        logger.info("Processing a single PDF file", file=files[0].filename)
    else:
        logger.info(f"Processing {len(files)} PDF files")

    file_names: List[str] = [file.filename for file in files]

    try:
        # Process the files through the pipeline
        pipeline = PDFExpertPreprocessingPipeline()
        logger.info("Start PDF processing pipeline", files=file_names)
        
        # Process complete pipeline - both S3 and Vector DB in a single transaction
        try:
            # Process PDFs through the pipeline
            chunks = await pipeline._run(pdf_files=files, metadatas=doc_metadata, s3_client=s3_client)
            
            if not chunks:
                logger.error("No documents were processed")
                failed_list.extend(file_names)
                return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}
            
            # Record successful processing
            for file in files:
                succeeded_list.append(file.filename)

        except Exception as processing_error:
            logger.error("Processing pipeline failed", error=str(processing_error), exc_info=True)
            for file_name in file_names:
                failed_list.append(file_name)
                error_messages.append({"file": file_name, "error": f"Processing failed: {str(processing_error)}"})

            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

    except Exception as e:
        err_msg = f"Error during batch PDF processing. {e}"
        logger.error(err_msg, exc_info=True)
        failed_list.extend(file_names)
        error_messages.append({"error": str(e)})

        return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

    return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}


@pdf_router.post("/pdf-expert/", response_model=PDFResponse, status_code=status.HTTP_200_OK)
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    s3_client: AsyncS3Client = Depends(get_s3_client),
):
    """
    Accepts user-submitted PDF files and processes them.
    Uploads to S3 and vector store, then returns success message with processed files.
    
    - **files**: List of PDF files to upload
    """
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=ServiceName.PREPROCESSING,
        function_name=FunctionName.DATA_PIPELINE,
    )

    try:
        logger.info("Received request to process PDF files")
        if not files:
            return exception_handler.handle_bad_request(
                e="No PDF files provided in the request.",
                extra={"files_count": 0},
            )

        # Create default metadata
        doc_metadata = []
        for file in files:
            doc_metadata.append(DocumentMetadata(
                source=file.filename,
                type="EXPERT_KNOWLEDGE",
                description="PDF",
                is_active=True,
                update_at=datetime.datetime.now()
            ))

        # Validation for PDF files
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return exception_handler.handle_bad_request(
                    e=f"Invalid file format: {file.filename}. Only PDF files are accepted.",
                    extra={"file": file.filename},
                )

        # Process PDFs synchronously to get results
        result = await process_pdfs(files, doc_metadata, s3_client)
        
        # Create success message with processed files
        if not result["succeeded"] and not result["failed"]:
            message = "Processing attempted but resulted in no successes or failures recorded."
        elif result["failed"] and not result["succeeded"]:
            message = f"Processing failed for all requested PDF files: {', '.join(result['failed'])}"
        elif result["failed"]:
            message = f"Processing completed with some errors. Succeeded: {', '.join(result['succeeded'])}. Failed: {', '.join(result['failed'])}"
        else:
            message = f"Successfully processed PDF files: {', '.join(result['succeeded'])}"

        return PDFResponse(message=message)
    except Exception as e:
        return exception_handler.handle_exception(
            e=str(e), 
            extra={"error": "Failed to process PDF upload request", "files": [f.filename for f in files] if files else []}
        )
