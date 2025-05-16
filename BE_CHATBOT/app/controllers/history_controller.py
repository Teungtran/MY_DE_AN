from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.base_config import APP_CONFIG
from services.dynamodb import DynamoHistory
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
CONVERSATION_TABLE_NAME = APP_CONFIG.postgres_config.table_name
DYNAMO_URL = APP_CONFIG.dynamo_config.url
TABLE_NAME = APP_CONFIG.dynamo_config.table_name
REGION_NAME = APP_CONFIG.dynamo_config.region_name


def get_dynamo_history():
    return DynamoHistory(
        endpoint_url=DYNAMO_URL,
        region_name=REGION_NAME,
        table_name=TABLE_NAME,
    )




async def fetch_conversation_history(
    conversation_id: str,
    limit: int,
    dynamo_history: DynamoHistory,
):
    log_context = {"conversation_id": conversation_id}
    logger.info("Fetching conversation history", **log_context)

    try:
        history = dynamo_history.get_conversation_history(conversation_id=conversation_id, limit=limit)
        return history
    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}", **log_context)
        return []
    except Exception as e:
        logger.error("Failed to retrieve conversation history", **log_context, error=str(e), exc_info=True)
        raise


@router.get("/{conversation_id}/history", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_history(
    conversation_id: str,
    limit: Optional[int] = Query(10, description="Number of history items to return"),
    dynamo_history: DynamoHistory = Depends(get_dynamo_history),
):
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.RAG,
    )
    log_ctx = {"conversation_id": conversation_id}

    try:
        logger.info("Received request to fetch history", **log_ctx)

        if not conversation_id:
            logger.warning("No conversation ID provided", **log_ctx)
            return exception_handler.handle_bad_request(e="No conversation ID provided.", extra={})

        history = await fetch_conversation_history(conversation_id, limit or 10, dynamo_history)

        # Check if history is empty
        if not history or (isinstance(history, list) and len(history) == 0):
            logger.info("No conversation history found for valid ID", **log_ctx)
            return {
                "status": "empty",
                "message": "Valid ID but History is empty",
                "history": history,
                "conversation_id": conversation_id,
                "limit": limit,
            }

        return {
            "status": "succeed",
            "conversation_id": conversation_id,
            "limit": limit,
            "history": history,
        }
    except Exception as e:
        logger.error("Unexpected error in get_history", **log_ctx, error=str(e), exc_info=True)
        return exception_handler.handle_exception(e=f"Failed to retrieve history: {str(e)}", extra=log_ctx)
