import datetime
import json
import os
import re
import tempfile
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, status
from config.base_config import APP_CONFIG
from schemas.urls import DocumentMetadata, UrlsRequest, UrlsResponse
from services.data_pipeline.recommend_preprocessing_pipeline import RecommendProcessingPipeline
from services.storage.s3 import AsyncS3Client, S3Input, get_s3_client
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.helpers.webhook import post_to_webhook
from utils.logger.logger import get_logger

logger = get_logger(__name__)
recommend_router = APIRouter(prefix="/url")

_BUCKET_NAME = APP_CONFIG.s3config.bucket_name
if _BUCKET_NAME is None:
    raise ValueError("BUCKET_NAME is not set in environment variables")
BUCKET_NAME: str = _BUCKET_NAME

WEBHOOK_URL: str = APP_CONFIG.webhook_config.url + APP_CONFIG.webhook_config.recommend_processed_endpoint


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


async def send_webhook_payload(succeeded_list: List[str], failed_list: List[str], error_messages: List[dict]):
    try:
        logger.info("Preparing webhook notification", webhook_url=WEBHOOK_URL)

        payload = {
            "succeeded_urls": succeeded_list,
            "failed_urls": failed_list,
            "error_urls": error_messages,
        }

        await post_to_webhook(WEBHOOK_URL, payload)

    except Exception as e:
        logger.error(
            "Webhook notification failed with unexpected error",
            webhook_url=WEBHOOK_URL,
            error=str(e),
            exc_info=True,
        )


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
        return
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
        if not documents:
            logger.error("No documents were processed")
            failed_list.extend(paths)
            final_message = "No documents were processed"
            if WEBHOOK_URL:
                await send_webhook_payload(succeeded_list, failed_list, [{"source": path} for path in paths])
            return

        # Process complete pipeline - both S3 and Qdrant in a single transaction
        try:
            # Save documents to S3
            logger.info("Starting S3 upload process")
            for idx, doc in enumerate(documents):
                url_md = doc.metadata.get("source")
                content_md = doc.page_content
                metadata = {
                    "source": url_md or "",
                    "processed_date": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                name = get_filename_from_url(url_md or "")
                md_filename = f"recommend_{name}_{idx}.md"
                with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".md") as md_file:
                    md_file.write(str(content_md))
                    md_file_path = md_file.name

                await s3_client.put_object(
                    S3Input(bucket_name=BUCKET_NAME, object_name=md_filename, file_path=md_file_path),
                    extra_args={"Metadata": metadata},
                )
                logger.info("Markdown content uploaded to S3 with metadata", s3_key=md_filename)
                total_docs = len(documents)
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
            # save to Qdrant
            await pipeline_url._run(paths=paths,preloaded_documents=documents)

            for idx, doc in enumerate(documents):
                url_md = doc.metadata.get("source")
                if url_md is not None:
                    succeeded_list.append(url_md)

        except Exception as processing_error:
            logger.error("Processing pipeline failed", error=str(processing_error), exc_info=True)
            for url in paths:
                failed_list.append(url)
                error_messages.append({"url": url, "error": f"Processing failed: {str(processing_error)}"})

            if WEBHOOK_URL:
                await send_webhook_payload(succeeded_list, failed_list, error_messages)

            return exception_handler.handle_exception(
                e=str(processing_error),
                extra={"error": "Processing pipeline failed", "urls": paths},
            )

    except Exception as e:
        err_msg = f"Error during batch URL processing. {e}"
        logger.error(err_msg, exc_info=True)
        failed_list.extend(paths)

        if WEBHOOK_URL:
            await send_webhook_payload(succeeded_list, failed_list, error_messages)

        return exception_handler.handle_exception(e=str(e), extra={"error urls": paths if paths else []})

    if not succeeded_list and not failed_list:
        final_message = "Processing attempted but resulted in no successes or failures recorded."
    elif failed_list and not succeeded_list:
        final_message = "Processing failed for all requested URLs."
    elif failed_list:
        final_message = "Processing completed with some errors."
    else:
        final_message = "Processing completed successfully. Check your Qdrant and S3."

    logger.info(
        f"Task completed: {final_message}",
        success_count=len(succeeded_list),
        failure_count=len(failed_list),
    )
    if WEBHOOK_URL:
        await send_webhook_payload(succeeded_list, failed_list, error_messages)


@recommend_router.post("/recommend/", response_model=UrlsResponse, status_code=status.HTTP_200_OK)
async def url_processing(
    request: UrlsRequest,
    background_tasks: BackgroundTasks,

    s3_client: AsyncS3Client = Depends(get_s3_client),
):
    """
    Accepts user-submitted URLs and processes them in the background. Uploads to S3 and notifies webhook.
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

        background_tasks.add_task(process_urls, request.urls, s3_client)

        logger.info("Background task added for URL processing", url_count=len(request.urls))
        return UrlsResponse(
            message=f"Submitted {len(request.urls)} URLs for processing. Check your webhook for results."
        )
    except FileNotFoundError as e:
        return exception_handler.handle_not_found_error(
            e=str(e), extra={"error urls": [url.source for url in request.urls] if request.urls else []}
        )
    except Exception as e:
        return exception_handler.handle_exception(
            e=str(e), extra={"error urls": [url.source for url in request.urls] if request.urls else []}
        )
