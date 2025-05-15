from datetime import timezone
from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from controllers.deps import SessionDep
from models.conversation import Conversation
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.logging.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# ---FastAPI App---
router = APIRouter(prefix="/init-conversation")


@router.post(
    "",  # POST request to the router's prefix
    status_code=201,  # HTTP 201 Created
    summary="Initialize a New Conversation",
    description="Generates a unique UUID, creates a new conversation record "
    "in the database with the title 'New chat', and returns "
    "the conversation ID and creation timestamp.",
)
async def initialize_conversation(
    session: SessionDep,
    # current_user: CurrentUser, # TODO: Inject authenticated user later
) -> JSONResponse:
    """
    Initializes a new conversation record using a generated UUID as the primary key.
    """

    # Initialize your custom exception handler for this endpoint context
    exception_handler = ExceptionHandler(
        logger=logger,
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.RAG,
    )

    logger.info("Attempting to initialize a new conversation.")

    try:
        # --- 1. Generate Conversation ID (UUID) ---
        generated_uuid = uuid4()
        logger.debug(f"Generated new conversation UUID: {generated_uuid}")

        # --- 2. Create Conversation Instance ---
        new_conversation = Conversation(
            id=generated_uuid,
            title="New chat",
            guest_id="TEST_GUEST_ID",
        )

        # --- 3. Save to PostgreSQL ---
        logger.debug(f"Adding conversation {generated_uuid} to session.")
        session.add(new_conversation)
        logger.debug(f"Committing session for conversation {generated_uuid}.")
        session.commit()
        # No refresh needed if we don't return DB-generated values
        logger.info(f"Successfully saved conversation {new_conversation.id} to the database.")

        # --- 4. Return Success Message ---
        success_message = "Conversation initialized successfully."
        logger.info(f"Returning success: '{success_message}'")

        created_at_db = new_conversation.created_at
        updated_at_db = new_conversation.updated_at
        created_at_iso = None
        if created_at_db:
            if created_at_db.tzinfo is None:
                created_at_db = created_at_db.replace(tzinfo=timezone.utc)
            created_at_iso = created_at_db.isoformat()

        updated_at_iso = None
        if updated_at_db:
            if updated_at_db.tzinfo is None:
                updated_at_db = updated_at_db.replace(tzinfo=timezone.utc)
            updated_at_iso = updated_at_db.isoformat()
        response_content = {
            "conversation_id": str(generated_uuid),
            "title": new_conversation.title,
            "created_at": created_at_iso,
            "updated_at": updated_at_iso,
        }

        return JSONResponse(content=response_content, status_code=status.HTTP_201_CREATED)

    except Exception as error:
        # --- 5. Handle Exceptions ---
        logger.error(f"Failed to initialize conversation: {error}", exc_info=True)
        # Delegate to your custom exception handler
        return exception_handler.handle_exception(
            e=str(error), extra={"message": "Failed to initialize conversation in the database."}
        )
