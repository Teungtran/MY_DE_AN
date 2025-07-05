import datetime
import os
import re
import tempfile
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, status

from config.base_config import APP_CONFIG
from schemas.urls import DocumentMetadata, UrlsRequest, UrlsResponse
from services.data_pipeline.store.url_rag_preprocessing_pipeline import URLRAGPreprocessingPipeline
from services.storage.s3 import AsyncS3Client, S3Input, get_s3_client
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.logger.logger import get_logger

logger = get_logger(__name__)
url_router = APIRouter(prefix="/url")

_BUCKET_NAME = APP_CONFIG.s3config.bucket_name
if _BUCKET_NAME is None:
    _BUCKET_NAME = "dataversion0205"  # Fallback to the value in test.py
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
        documents = await pipeline_url._get_documents(paths=paths, metadatas=doc_metadata)

        if not documents:
            logger.error("No documents were processed")
            failed_list.extend(paths)
            return {"succeeded": succeeded_list, "failed": failed_list, "error_messages": error_messages}

        # Process complete pipeline - both S3 and Vector DB in a single transaction
        try:
            # Save documents to S3
            logger.info("Starting S3 upload process")
            for idx, doc in enumerate(documents):
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
            # save to Vector DB
            await pipeline_url._run(paths=paths, metadatas=doc_metadata, preloaded_documents=documents)

            for idx, doc in enumerate(documents):
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
        
        # Create success message with processed URLs
        if not result["succeeded"] and not result["failed"]:
            message = "Processing attempted but resulted in no successes or failures recorded."
        elif result["failed"] and not result["succeeded"]:
            message = f"Processing failed for all requested URLs: {', '.join(result['failed'])}"
        elif result["failed"]:
            message = f"Processing completed with some errors. Succeeded: {', '.join(result['succeeded'])}. Failed: {', '.join(result['failed'])}"
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
