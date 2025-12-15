import datetime
import os
import re
import tempfile
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, status
from langchain.schema import Document

from app.config.base_config import APP_CONFIG
from app.schemas.urls import DocumentMetadata, UrlsRequest, UrlsResponse
from app.services.data_pipeline.store.url_rag_preprocessing_pipeline import URLRAGPreprocessingPipeline
from app.services.storage.s3 import AsyncS3Client, S3Input, get_s3_client
from app.utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from app.utils.logger.logger import get_logger

logger = get_logger(__name__)
url_router = APIRouter(prefix="/url")

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


async def process_urls(doc_metadata: List[DocumentMetadata], s3_client: AsyncS3Client):
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
        pipeline_url = URLRAGPreprocessingPipeline(type="urls")
        logger.info("Start URL processing pipeline", url=paths)
        # get content from URLs
        raw_documents = await pipeline_url._get_documents(paths=paths, metadatas=doc_metadata)

        if not raw_documents:
            logger.error("No documents were processed")
            failed_list.extend(paths)
            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

        # Separate valid documents from failed ones (guardrail failures, etc.)
        valid_documents = []
        failed_documents = []
        
        for idx, doc in enumerate(raw_documents):
            if isinstance(doc, str):
                # This is an error string (guardrail failure, etc.)
                source_url = paths[idx] if idx < len(paths) else "Unknown URL"
                error_msg = doc
                failed_documents.append({"url": source_url, "error": error_msg})
                failed_list.append(source_url)
                error_messages.append({"url": source_url, "error": error_msg})
                logger.warning(f"Document processing failed for {source_url}: {error_msg}")
            elif isinstance(doc, Document):
                valid_documents.append(doc)
            else:
                # Unknown type
                source_url = paths[idx] if idx < len(paths) else "Unknown URL"
                error_msg = "Unknown document type returned"
                failed_documents.append({"url": source_url, "error": error_msg})
                failed_list.append(source_url)
                error_messages.append({"url": source_url, "error": error_msg})
                logger.warning(f"Document processing failed for {source_url}: {error_msg}")
        
        if not valid_documents and failed_documents:
            # All documents failed
            logger.error(f"All {len(failed_documents)} documents failed processing")
            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}
        
        if not valid_documents:
            logger.error("No valid documents were processed")
            failed_list.extend(paths)
            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

        try:
            # Save documents to S3
            logger.info(f"Starting S3 upload process for {len(valid_documents)} valid documents")
            for idx, doc in enumerate(valid_documents):
                url_md = doc.metadata.get("source")
                content_md = doc.page_content
                metadata = {
                    "source": url_md or "",
                    "description": doc.metadata.get("description") or "",
                    "type": doc.metadata.get("type") or "",
                    "processed_date": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                name = get_filename_from_url(url_md or "")
                md_filename = f"policy/processed_rag_data_{name}_{idx}_from_url.md"
                with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".md") as md_file:
                    md_file.write(str(content_md))
                    md_file_path = md_file.name

                await s3_client.put_object(
                    S3Input(bucket_name=BUCKET_NAME, object_name=md_filename, file_path=md_file_path),
                    extra_args={"Metadata": metadata},
                )
                logger.info("Markdown content uploaded to S3 with metadata", s3_key=md_filename)
                try:
                    os.remove(md_file_path)
                except Exception as cleanup_error:
                    logger.warning(
                        "Failed to clean up temporary file",
                        tmp_file=md_file_path,
                        error=str(cleanup_error),
                    )
            
            # Get valid URLs for pipeline
            valid_urls = [doc.metadata.get("source") for doc in valid_documents if doc.metadata.get("source")]
            # Match metadata by finding the index of each valid URL in the original paths
            valid_metadatas = []
            for url in valid_urls:
                try:
                    idx = paths.index(url)
                    if idx < len(doc_metadata):
                        valid_metadatas.append(doc_metadata[idx])
                except ValueError:
                    pass
            
            # save to Vector DB
            await pipeline_url._run(paths=valid_urls, metadatas=valid_metadatas, preloaded_documents=valid_documents)

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


@url_router.post("/urls-rag/", response_model=UrlsResponse, status_code=status.HTTP_200_OK)
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
        result = await process_urls(request.urls, s3_client)
        
        guardrail_errors = [e for e in result.get("error_messages", []) if "Guardrail" in str(e.get("error", "")) or "INVALID DATA" in str(e.get("error", ""))]
        other_errors = [e for e in result.get("error_messages", []) if e not in guardrail_errors]
        
        # Create success message with processed URLs
        if not result["succeeded"] and not result["failed"]:
            message = "Processing attempted but resulted in no successes or failures recorded."
        elif result["failed"] and not result["succeeded"]:
            # All failed
            if guardrail_errors:
                guardrail_urls = [e.get("url", "Unknown") for e in guardrail_errors]
                message = f"Guardrail verification failed for all URLs: {', '.join(guardrail_urls)}. Content does not match requirements."
            else:
                error_details = [f"{e.get('url', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in result.get("error_messages", [])]
                message = f"Processing failed for all requested URLs: {', '.join(result['failed'])}. Errors: {'; '.join(error_details)}"
        elif result["failed"]:
            # Some succeeded, some failed
            success_msg = f"Succeeded: {', '.join(result['succeeded'])}"
            if guardrail_errors:
                guardrail_urls = [e.get("url", "Unknown") for e in guardrail_errors]
                message = f"{success_msg}. Guardrail verification failed for: {', '.join(guardrail_urls)} (Content does not match requirements)."
                if other_errors:
                    other_details = [f"{e.get('url', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in other_errors]
                    message += f" Other errors: {'; '.join(other_details)}"
            else:
                error_details = [f"{e.get('url', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in result.get("error_messages", [])]
                message = f"{success_msg}. Failed: {', '.join(result['failed'])}. Errors: {'; '.join(error_details)}"
        else:
            message = f"Successfully processed URLs: {', '.join(result['succeeded'])}"

        return UrlsResponse(message=message)
    except FileNotFoundError as e:
        return exception_handler.handle_not_found_error(
            e=str(e), extra={"error urls": [url.source for url in request.urls] if request.urls else []}
        )
    except Exception as e:
        return exception_handler.handle_exception(
            e=str(e), extra={"error urls": [url.source for url in request.urls] if request.urls else []}
        )
