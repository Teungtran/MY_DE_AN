import datetime
import json
import os
import re
import tempfile
from typing import List,Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, status
from app.config.base_config import APP_CONFIG
from app.schemas.urls import DocumentMetadata, UrlsRequest, UrlsResponse
from app.services.data_pipeline.store.recommend_preprocessing_pipeline import RecommendProcessingPipeline
from app.services.storage.s3 import AsyncS3Client, S3Input, get_s3_client
from app.utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from app.utils.logger.logger import get_logger
from app.utils.db_check import check_device_exists

logger = get_logger(__name__)
recommend_router = APIRouter(prefix="/url")

_BUCKET_NAME = APP_CONFIG.s3config.bucket_name
if _BUCKET_NAME is None:
    _BUCKET_NAME = "dataversion0204"  # Fallback to the value in test.py
BUCKET_NAME: str = _BUCKET_NAME


def get_filename_from_url(url: str) -> str:
    path = urlparse(url).path
    if not path or path == "/":
        return "index"
    # Extract last 1–2 meaningful parts of the path
    parts = [p for p in path.strip("/").split("/") if p]
    filename_base = "-".join(parts[-2:]) if len(parts) >= 2 else parts[0]
    # Replace any characters that aren't safe in filenames
    filename_safe = re.sub(r"[^a-zA-Z0-9\-_.]", "-", filename_base)
    return filename_safe


async def process_urls(doc_metadata: List[DocumentMetadata], s3_client: AsyncS3Client, replace_existing: bool = False, device_names_to_replace: List[str] = None, skip_duplicate_check: bool = False):
    exception_handler = ExceptionHandler(
        logger=logger.bind(), service_name=ServiceName.PREPROCESSING, function_name=FunctionName.DATA_PIPELINE
    )

    logger.info("Processing user-submitted URLs")
    succeeded_list: List[str] = []
    failed_list: List[str] = []
    error_messages = []

    if not doc_metadata:
        logger.error("No URLs found")
        return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}
        
    if len(doc_metadata) == 1:
        logger.info("Processing a single URL", url=doc_metadata[0].source)
    else:
        logger.info(f"Processing {len(doc_metadata)} URLs")

    paths: List[str] = [url.source for url in doc_metadata if url.source is not None]

    try:
        pipeline_url = RecommendProcessingPipeline()
        logger.info("Start URL processing pipeline", url=paths)
        raw_data = await pipeline_url._get_documents(urls=paths)
        documents = await pipeline_url._batch_process_documents(raw_data)
        
        # Separate valid documents from failed ones (guardrail failures, etc.)
        valid_documents = []
        failed_documents = []
        
        for doc in documents:
            if doc.metadata.get("processing_failed") or doc.metadata.get("error"):
                # Document failed processing (guardrail, etc.)
                error_msg = doc.metadata.get("error", "Unknown processing error")
                source_url = doc.metadata.get("source", "Unknown URL")
                failed_documents.append({"url": source_url, "error": error_msg})
                failed_list.append(source_url)
                error_messages.append({"url": source_url, "error": error_msg})
                logger.warning(f"Document processing failed for {source_url}: {error_msg}")
            else:
                valid_documents.append(doc)
        
        if not valid_documents and failed_documents:
            # All documents failed
            logger.error(f"All {len(failed_documents)} documents failed processing")
            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}
        
        if not valid_documents:
            logger.error("No valid documents were processed")
            failed_list.extend(paths)
            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}
        
        # Determine which device names to replace (if any)
        devices_to_replace_list = None
        
        # Check if any devices already exist in database (only if not replacing and not skipping check)
        if not replace_existing and not skip_duplicate_check:
            existing_devices = []
            for doc in valid_documents:
                device_name = doc.metadata.get("device_name")
                if device_name and check_device_exists(device_name):
                    existing_devices.append(device_name)
            
            if existing_devices:
                # Return all existing devices for confirmation
                device_list = ", ".join(f"'{d}'" for d in existing_devices)
                logger.info(f"Devices already exist in database: {device_list}")
                return {
                    "succeeded": succeeded_list, 
                    "failed": failed_list, 
                    "error_messages": error_messages,
                    "confirmation_required": True,
                    "device_name": existing_devices[0],  # Return first for backward compatibility
                    "existing_devices": existing_devices  # Return all existing devices
                }
        elif skip_duplicate_check or replace_existing:
            # If skipping duplicate check or explicitly replacing, extract device names to replace
            devices_to_replace_list = []
            for doc in valid_documents:
                device_name = doc.metadata.get("device_name")
                if device_name:
                    devices_to_replace_list.append(device_name)
            
            if devices_to_replace_list:
                device_list = ", ".join(f"'{d}'" for d in devices_to_replace_list)
                logger.info(f"Will replace existing data for devices: {device_list}")
            else:
                logger.warning("No device names found in documents for replacement")

        # Process complete pipeline - both S3 and Vector DB in a single transaction
        try:
            # Save documents to S3 (only valid documents)
            logger.info(f"Starting S3 upload process for {len(valid_documents)} valid documents")
            for idx, doc in enumerate(valid_documents):
                url_md = doc.metadata.get("source")
                content_md = doc.page_content
                metadata = {
                    "source": url_md or "",
                    "processed_date": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                name = get_filename_from_url(url_md or "")
                md_filename = f"store_product/recommend_{name}_{idx}.md"
                with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".md") as md_file:
                    md_file.write(str(content_md))
                    md_file_path = md_file.name

                await s3_client.put_object(
                    S3Input(bucket_name=BUCKET_NAME, object_name=md_filename, file_path=md_file_path),
                    extra_args={"Metadata": metadata},
                )
                logger.info("Markdown content uploaded to S3 with metadata", s3_key=md_filename)
                total_docs = len(valid_documents)
                progress = ((idx + 1) / total_docs) * 100
                logger.info(f"Uploading progress: {progress:.2f}% ({idx + 1}/{total_docs})")
                try:
                    os.remove(md_file_path)
                except Exception as cleanup_error:
                    logger.warning(
                        "Failed to clean up temporary file",
                        tmp_file=md_file_path,
                        error=str(cleanup_error),
                    )
            
            valid_urls = [doc.metadata.get("source") for doc in valid_documents if doc.metadata.get("source")]
            
            await pipeline_url._run(
                paths=valid_urls, 
                preloaded_documents=valid_documents,
                device_names_to_replace=devices_to_replace_list
            )

            for doc in valid_documents:
                url_md = doc.metadata.get("source")
                if url_md is not None:
                    succeeded_list.append(url_md)

        except Exception as processing_error:
            logger.error("Processing pipeline failed", error=str(processing_error), exc_info=True)
            for url in paths:
                failed_list.append(url)
                error_messages.append({"url": url, "error": f"Processing failed: {str(processing_error)}"})

            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

    except Exception as e:
        err_msg = f"Error during batch URL processing. {e}"
        logger.error(err_msg, exc_info=True)
        failed_list.extend(paths)
        error_messages.append({"error": str(e)})

        return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

    return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}


@recommend_router.post("/recommend/", response_model=UrlsResponse, status_code=status.HTTP_200_OK)
async def url_processing(
    request: UrlsRequest,
    s3_client: AsyncS3Client = Depends(get_s3_client),
):
    """
    Accepts user-submitted URLs and processes them.
    Uploads to S3 and vector store, then returns success message with processed URLs.
    """
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=ServiceName.PREPROCESSING,
        function_name=FunctionName.DATA_PIPELINE,
    )

    try:
        logger.info("Received request to process URLs")
        if not request.urls:
            return exception_handler.handle_bad_request(
                e="No URLs provided in the request.",
                extra={"payload": request.model_dump()},
            )

        #  validation for URLs
        for url_metadata in request.urls:
            if not url_metadata.source or not url_metadata.source.startswith(("http://", "https://")):
                return exception_handler.handle_bad_request(
                    e=f"Invalid URL format: {url_metadata.source}",
                    extra={"payload": request.model_dump()},
                )

        # Process URLs synchronously to get results
        result = await process_urls(request.urls, s3_client, skip_duplicate_check=request.skip_duplicate_check)
        
        # Check if confirmation is required
        if result.get("confirmation_required"):
            device_name = result.get("device_name")
            existing_devices = result.get("existing_devices", [device_name])
            
            if len(existing_devices) == 1:
                message = f"Device '{existing_devices[0]}' already exists in the database. Please confirm if you want to replace the existing data."
            else:
                device_list = ", ".join(f"'{d}'" for d in existing_devices)
                message = f"{len(existing_devices)} devices already exist in the database: {device_list}. Please confirm if you want to replace the existing data for all of them."
            
            return UrlsResponse(
                message=message,
                status="confirmation_required",
                device_name=device_name,
                existing_devices=existing_devices
            )
        
        # Create success message with processed URLs
        guardrail_errors = [e for e in result.get("error_messages", []) if "Guardrail" in str(e.get("error", "")) or "INVALID DATA" in str(e.get("error", ""))]
        other_errors = [e for e in result.get("error_messages", []) if e not in guardrail_errors]
        
        if not result["succeeded"] and not result["failed"]:
            message = "Processing attempted but resulted in no successes or failures recorded."
        elif result["failed"] and not result["succeeded"]:
            # All failed
            if guardrail_errors:
                guardrail_urls = [e.get("url", "Unknown") for e in guardrail_errors]
                message = f"Guardrail verification failed for all URLs: {', '.join(guardrail_urls)}. Content does not match FPT Shop product requirements."
            else:
                error_details = [f"{e.get('url', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in result.get("error_messages", [])]
                message = f"Processing failed for all requested URLs: {', '.join(result['failed'])}. Errors: {'; '.join(error_details)}"
        elif result["failed"]:
            # Some succeeded, some failed
            success_msg = f"Succeeded: {', '.join(result['succeeded'])}"
            if guardrail_errors:
                guardrail_urls = [e.get("url", "Unknown") for e in guardrail_errors]
                message = f"{success_msg}. Guardrail verification failed for: {', '.join(guardrail_urls)} (Content does not match FPT Shop product requirements)."
                if other_errors:
                    other_details = [f"{e.get('url', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in other_errors]
                    message += f" Other errors: {'; '.join(other_details)}"
            else:
                error_details = [f"{e.get('url', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in result.get("error_messages", [])]
                message = f"{success_msg}. Failed: {', '.join(result['failed'])}. Errors: {'; '.join(error_details)}"
        else:
            message = f"Successfully processed URLs: {', '.join(result['succeeded'])}"

        return UrlsResponse(message=message, status="success")
    except FileNotFoundError as e:
        return exception_handler.handle_not_found_error(
            e=str(e), extra={"error urls": [url.source for url in request.urls] if request.urls else []}
        )
    except Exception as e:
        return exception_handler.handle_exception(
            e=str(e), extra={"error urls": [url.source for url in request.urls] if request.urls else []}
        )
