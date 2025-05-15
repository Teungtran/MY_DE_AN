import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Union, cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langdetect import detect

from config.base_config import APP_CONFIG
from orchestrator.graphs.agentic_graph.graph import graph
from orchestrator.tools.retriever import retriever_tool
from schemas.chunk_message import Artifact, ChunkMessage
from schemas.user_inputs import UserInputs
from services.dynamodb import DynamoHistory
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.logging.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# ---FastAPI App---
router = APIRouter()

# ---Initialize database config
DYNAMO_URL = APP_CONFIG.dynamo_config.url
TABLE_NAME = APP_CONFIG.dynamo_config.table_name
REGION_NAME = APP_CONFIG.dynamo_config.region_name

manager: Optional[DynamoHistory] = None

try:
    manager = DynamoHistory(
        endpoint_url=DYNAMO_URL,
        table_name=TABLE_NAME,
        region_name=REGION_NAME,
    )
    logger.info("DynamoHistory initialized successfully")
except Exception as init_exc:
    logger.error("Error initializing DynamoHistory", exc_info=init_exc)


FLAG_GET_CONFIRM_FROM_CLIENT = False


async def event_stream(user_inputs: UserInputs, config: Dict):
    # Initialize the exception handler with service and function name
    try:
        start_time = datetime.datetime.now(datetime.timezone.utc)
        conversation_id = user_inputs.conversation_id
        logger.info(f"Starting event_stream: conversation_id={conversation_id}")

        original_message = user_inputs.message
        args = cast(Dict[Any, Any], user_inputs.args or {})
        raw_category = user_inputs.category_code
        metadata_history = None

        if isinstance(raw_category, dict) and "category_id" in raw_category and "category_name" in raw_category:
            metadata_history = {
                "id": raw_category["category_id"],
                "name": raw_category["category_name"],
            }
        tool_call_name = None
        tool_call_args = None
        tool_call_id = None
        tool_call_type = None
        history_lang = None
        prompt_token = 0
        completion_token = 0
        # Detect language of the message
        history_lang = detect(original_message) if original_message else None

        # Check if we need to handle a tool response
        message: Union[str, ToolMessage, HumanMessage] = original_message
        snapshot = graph.get_state(config, subgraphs=True)

        if snapshot and snapshot.next:
            last_toolcall_message = None
            # Find last message with tool calls
            if "messages" in snapshot.tasks[0].state.values:
                last_message = snapshot.tasks[0].state.values["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    last_toolcall_message = last_message

            if last_toolcall_message:
                # Handle user's response to tool call
                if original_message.strip().lower() == "y":
                    # User approved the tool call
                    if args and last_toolcall_message.tool_calls[0]["args"] != args:
                        last_toolcall_message.tool_calls[0]["args"].update(args)
                        
                        graph.update_state(
                            snapshot.tasks[0].state.config,
                            {"messages": last_toolcall_message},
                        )

                    message = None  # Continue with default execution
                else:
                    # User provided feedback
                    message = ToolMessage(
                        tool_call_id=last_toolcall_message.tool_calls[0]["id"],
                        content=f"API call denied by user. Reasoning: '{original_message}'. Continue assisting, accounting for the user's input.",
                    )
            else:
                # No tool calls found but snapshot.next is True - unexpected state
                logger.warning(
                    f"Unexpected state: snapshot.next is True but no tool calls found for conversation_id={conversation_id}"
                )
                message = HumanMessage(content=original_message)
        else:
            # Regular message from user
            message = ("user", original_message)

        # Prepare input for graph
        graph_input = {"messages": message} if message is not None else None

        # Stream graph response
        artifact = None
        msg_id = None

        # Stream the response messages
        async for node_name, (msg, metadata) in graph.astream(
            graph_input, config, stream_mode="messages", subgraphs=True
        ):
            if isinstance(msg, AIMessage) and msg.content:
                msg_id = getattr(msg, "id", None)
                print(msg.content, end="|")

                # Send message chunk
                payload = ChunkMessage(
                    content=msg.content, args={}, name="agent", type="message_chunk", id=msg_id, finishReason=""
                )
                yield f"data: {payload.model_dump_json()} \n\n"

        final_state = graph.get_state(config, subgraphs=True)
        state_messages = []
        if final_state.next:
            state_messages = final_state.tasks[0].state.values["messages"]
        else:
            state_messages = final_state.values["messages"]

        state_messages = state_messages[::-1]

        last_ai_message = None
        for msg in state_messages:
            if isinstance(msg, AIMessage):
                last_ai_message = msg
                break

        last_toolcall_message = None
        for msg in state_messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                last_toolcall_message = msg
                break

        last_tool_message = None
        if last_toolcall_message:
            for msg in state_messages:
                if isinstance(msg, ToolMessage) and msg.tool_call_id == last_toolcall_message.tool_calls[0]["id"]:
                    last_tool_message = msg
                    break

        artifact = Artifact()
        if last_toolcall_message:
            tool_call_name = last_toolcall_message.tool_calls[0]["name"]
            tool_call_args = last_toolcall_message.tool_calls[0]["args"]
            tool_call_id = last_toolcall_message.tool_calls[0]["id"]
            tool_call_type = last_toolcall_message.tool_calls[0]["type"]
            artifact.form = tool_call_args
        if last_tool_message:
            if last_tool_message.name != retriever_tool.name:
                artifact.data = last_tool_message.content
            if last_tool_message.artifact:
                artifact.sources = last_tool_message.artifact

        payload = ChunkMessage(
            name=str(last_toolcall_message.tool_calls[0]["name"]) if last_toolcall_message else "agent",
            type="artifact",
            id=last_ai_message.id,
            finishReason="stop",
            content="",
            language=history_lang,
            artifact=artifact,
        )
        yield f"data: {payload.model_dump_json()} \n\n"

        end_time = datetime.datetime.now(datetime.timezone.utc)
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Stream finished, execution_time={execution_time}s")
        
        # Debug: print the full final_state
        print("FINAL STATE TYPE:", type(final_state))
        print("FINAL STATE DIR:", dir(final_state))
        print("FINAL STATE:", final_state)
        
        prompt_token = 0
        completion_token = 0
        # Safely extract tokens
        if hasattr(final_state, 'tasks') and final_state.tasks:
            try:
                prompt_token = final_state.tasks[0].state.values.get("prompt_token", 0)
                completion_token = final_state.tasks[0].state.values.get("completion_token", 0)
            except Exception as e:
                print("Error extracting tokens from tasks[0]:", e)
        elif hasattr(final_state, 'values'):
            prompt_token = final_state.values.get("prompt_token", 0)
            completion_token = final_state.values.get("completion_token", 0)
        else:
            print("final_state has no tasks or values attribute!")
        total_token = prompt_token + completion_token
        logger.info(f"Token usage - prompt: {prompt_token}, completion: {completion_token}, total: {total_token}")
        print(f"Token usage - prompt: {prompt_token}, completion: {completion_token}, total: {total_token}")
        # Save to history database
        if manager and last_ai_message:
            try:
                decimal_execution_time = Decimal(str(execution_time)) if execution_time is not None else None
                if not 'tool_call_name' in locals():
                    tool_call_name = None
                if not 'tool_call_args' in locals():
                    tool_call_args = None
                if not 'tool_call_id' in locals():
                    tool_call_id = None
                if not 'tool_call_type' in locals():
                    tool_call_type = None
                # Save history entry
                manager.save_chat_history(
                    conversation_id=conversation_id,
                    user_input=original_message,
                    prompt_token=prompt_token,
                    completion_token=completion_token,
                    total_token=total_token,
                    end_time=end_time,
                    start_time=start_time,
                    execution_time=decimal_execution_time,
                    language=history_lang,
                    tool_call_name=tool_call_name,
                    tool_call_args=tool_call_args,
                    tool_call_id=tool_call_id,
                    tool_call_type=tool_call_type,
                    response=last_ai_message.content if hasattr(last_ai_message, "content") else None,
                    category_id=metadata_history.get("id") if metadata_history else None,
                    category_name=metadata_history.get("name") if metadata_history else None,
                    source=artifact.sources if artifact else None,
                )
                logger.info("Chat history saved successfully")
            except Exception as save_exc:
                logger.error("Error saving chat history to DynamoDB", exc_info=save_exc)
        else:
            if not manager:
                logger.warning("DynamoDB not initialized; skipping save to history.")
            elif not last_ai_message:
                logger.warning("No last message available; skipping save to history.")
    except Exception as exc:
        logger.error("Error in event_stream", exc_info=exc)
        error_payload = ChunkMessage(
            content=f"An error occurred: {str(exc)}",
            name="error",
            type="error",
            id="error",
            finishReason="error",
        )
        yield f"data: {error_payload.model_dump_json()} \n\n"
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/streaming-answer")
async def stream(user_inputs: UserInputs):
    exception_handler = ExceptionHandler(
        logger=logger,
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.RAG,
    )
    try:
        logger.info(f"Received /stream request: conversation_id={user_inputs.conversation_id}")
        config = {"configurable": {"thread_id": user_inputs.conversation_id}, "recursion_limit": 10}
        return StreamingResponse(event_stream(user_inputs, config), media_type="text/event-stream")
    except Exception as exc:
        # Handle errors when initiating stream
        logger.error("Error in stream endpoint", exc_info=exc)
        return exception_handler.handle_exception(e=str(exc), extra={"user_inputs": user_inputs.model_dump()})