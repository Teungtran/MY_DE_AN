import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langdetect import detect

from config.base_config import APP_CONFIG
from orchestrator.graphs.rag_graph.graph import GraphBuilder
from schemas.chunk_message import Artifact, ChunkMessage
from schemas.user_inputs import RoleEnum, UserInputs
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


generator = GraphBuilder()
graph = generator.graph


FLAG_GET_CONFIRM_FROM_CLIENT = False


async def event_stream(user_inputs: UserInputs, config: Dict):
    # Initialize the exception handler with service and function name
    try:
        start_time = datetime.datetime.now(datetime.timezone.utc)
        conversation_id = user_inputs.conversation_id
        logger.info(f"Starting event_stream: conversation_id={conversation_id}")

        message = user_inputs.message
        args = cast(Dict[Any, Any], user_inputs.args)
        role: str = ""
        assistant_response: str = ""
        artifact = None
        raw_category = args.get("category_code")
        metadata_history = None

        if isinstance(raw_category, dict) and "category_id" in raw_category and "category_name" in raw_category:
            metadata_history = {
                "id": raw_category["category_id"],
                "name": raw_category["category_name"],
            }
        # Initialize tool call variables
        tool_calls_name = None
        tool_calls_args = None
        tool_calls_id = None
        tool_calls_type = None
        lang_detected = None
        finish_reason = None
        history_tool_args = None
        history_lang = None
        history_lang = detect(message)
        # tool_response = None
        if role == RoleEnum.CLIENT and FLAG_GET_CONFIRM_FROM_CLIENT:
            print("hi message from client need to confirm xxxxxxxx")
            print(f"args: {args}")

            metadata = graph.get_state(config).values["messages"][-1]
            print(f"metadata: {metadata}")
            current_content = metadata.content
            current_id = metadata.id
            tools_call_id = metadata.tool_calls[0]["id"]
            tools_call_name = metadata.tool_calls[0]["name"]

            if tools_call_name == "search_flight_schedule_workflow":
                new_message = {
                    "role": "assistant",
                    "content": current_content,
                    "tool_calls": [
                        {
                            "id": tools_call_id,
                            "name": tools_call_name,
                            "args": {
                                "origin": args["origin"],
                                "destination": args["destination"],
                                "departure_date": args["departure_date"],
                            },
                        }
                    ],
                    "id": current_id,
                }

            elif tools_call_name == "search_flight_info_workflow":
                new_message = {
                    "role": "assistant",
                    "content": current_content,
                    "tool_calls": [
                        {
                            "id": tools_call_id,
                            "name": tools_call_name,
                            "args": {
                                "marketing_airline_code": args["marketing_airline_code"],
                                "flight_number": args["flight_number"],
                                "departure_date": args["departure_date"],
                            },
                        }
                    ],
                    "id": current_id,
                }

            graph.update_state(
                config,
                {"messages": [new_message]},
                as_node="human_review_node",
            )

            assistant_response = ""
            # Stream tool response
            async for msg, metadata in graph.astream(None, config, stream_mode="messages"):
                if msg.content:  # Only process non-empty content
                    print(msg.content, end="|")
                    assistant_response += msg.content

                    payload = ChunkMessage(
                        content=msg.content, args={}, name="agent", type="message_chunk", id=msg.id, finishReason=""
                    )

                    yield f"data: {payload.model_dump_json()} \n\n"

            # Handle artifact if present after streaming is complete
            try:
                artifact = graph.get_state(config).values["messages"][-2].artifact
                if artifact:
                    payload = ChunkMessage(
                        content="",
                        args={},
                        name=tools_call_name,
                        type="artifact",
                        id=msg.id,
                        finishReason="stop",
                        artifact=artifact,
                    )
                    yield f"data: {payload.model_dump_json()} \n\n"
                else:
                    # Only send stop message if no artifact
                    payload = ChunkMessage(
                        content="", args={}, name="agent", type="message_chunk", id=msg.id, finishReason="stop"
                    )
                    yield f"data: {payload.model_dump_json()} \n\n"
            except (IndexError, AttributeError) as e:
                print(f"Error retrieving artifact: {e}")
                # Fallback stop message if error
                payload = ChunkMessage(
                    content="", args={}, name="agent", type="message_chunk", id=msg.id, finishReason="stop"
                )
                yield f"data: {payload.model_dump_json()} \n\n"

        else:
            first = True
            has_artifact = False
            final_msg_id = None

            async for msg, metadata in graph.astream({"messages": message}, config, stream_mode="messages"):
                if first:
                    gathered = msg
                    first = False
                else:
                    gathered = gathered + msg

                final_msg_id = msg.id

                # Handle tool calls
                if (
                    not gathered.content
                    and gathered.response_metadata  # noqa
                    and gathered.response_metadata["finish_reason"] == "tool_calls"  # noqa
                ):
                    tool_calls = gathered.tool_calls[0] or None
                    tool_calls_name = gathered.tool_calls[0]["name"] or None
                    current_content = gathered.content
                    current_id = gathered.id
                    tool_calls_id = tool_calls["id"] if tool_calls and "id" in tool_calls else None
                    tool_calls_args = tool_calls["args"] if tool_calls and "args" in tool_calls else None
                    tool_calls_type = tool_calls["type"] if tool_calls and "type" in tool_calls else None
                    finish_reason = None
                    if gathered and gathered.response_metadata and "finish_reason" in gathered.response_metadata:
                        finish_reason = gathered.response_metadata["finish_reason"]

                    print(f"tool_calls_name: {tool_calls_name}")

                    if tool_calls_name in ["search_flight_schedule_workflow", "search_flight_info_workflow"]:
                        assistant_response = ""  # NO AI RESPONSE
                        history_tool_args = tool_calls_args.copy() if tool_calls_args else {}

                        new_message = {
                            "role": "assistant",
                            "content": current_content,
                            "tool_calls": [
                                {
                                    "id": tool_calls_id,
                                    "name": tool_calls_name,
                                    "args": tool_calls_args,
                                }
                            ],
                            "id": current_id,
                        }

                        graph.update_state(
                            config,
                            {"messages": [new_message]},
                            as_node="human_review_node",
                        )

                        user_question: str = graph.get_state(config).values["messages"][-2].content
                        lang_detected = detect(user_question)
                        history_lang = lang_detected.copy() if hasattr(lang_detected, "copy") else lang_detected

                        print(f"lang detect: {lang_detected}")

                        # Prepare Payload
                        if tool_calls_name == "search_flight_schedule_workflow" and tool_calls_args:
                            payload = ChunkMessage(
                                content="",
                                language=lang_detected,
                                args={
                                    "origin": tool_calls_args.get("origin", ""),
                                    "destination": tool_calls_args.get("destination", ""),
                                    "departure_date": tool_calls_args.get("departure_date", ""),
                                },
                                name=tool_calls_name,
                                type=tool_calls_type or "",
                                id=tool_calls_id or "",
                                finishReason=finish_reason or "",
                            )
                        elif tool_calls_name == "search_flight_info_workflow" and tool_calls_args:
                            payload = ChunkMessage(
                                content="",
                                language=lang_detected,
                                args={
                                    "marketing_airline_code": tool_calls_args.get("marketing_airline_code", ""),
                                    "flight_number": tool_calls_args.get("flight_number", ""),
                                    "departure_date": tool_calls_args.get("departure_date", ""),
                                },
                                name=tool_calls_name,
                                type=tool_calls_type or "",
                                id=tool_calls_id or "",
                                finishReason=finish_reason or "",
                            )

                        # Serialize the payload into JSON and yield
                        yield f"data: {payload.model_dump_json()} \n\n"

                        # Handle case where we don't get confirmation from user
                        if not FLAG_GET_CONFIRM_FROM_CLIENT:
                            content = "User aborts this task, do not take this into context."
                            tool_message = [
                                {
                                    "tool_call_id": tool_calls_id,
                                    "type": "tool",
                                    "content": content,
                                }
                            ]

                            graph.update_state(
                                config,
                                {"messages": tool_message},
                                as_node="human_review_node",
                            )

                        break

                # Check if this message has content
                if msg.content:
                    print(msg.content, end="|")
                    assistant_response += msg.content

                    # Send message chunk with empty finishReason
                    payload = ChunkMessage(
                        content=msg.content, args={}, name="agent", type="message_chunk", id=msg.id, finishReason=""
                    )

                    yield f"data: {payload.model_dump_json()} \n\n"

                # Check if the message has an artifact
                if hasattr(msg, "artifact") and msg.artifact:
                    has_artifact = True
                    artifact = msg.artifact

            # After streaming all message chunks, check if we need to send artifact or stop
            try:
                # If we didn't find artifact in streaming, try to get it from graph state
                if not has_artifact:
                    try:
                        artifact = graph.get_state(config).values["messages"][-2].artifact
                        if artifact:
                            has_artifact = True
                    except (IndexError, AttributeError):
                        pass

                # If we have an artifact, send it with finishReason="stop"
                if has_artifact and artifact:
                    if tool_calls_name == "retrieve_information":
                        artifact_payload = Artifact(sources=artifact)
                    else:
                        artifact_payload = artifact

                    payload = ChunkMessage(
                        content="",
                        args={},
                        name="agent",
                        type="artifact",
                        id=str(final_msg_id),
                        finishReason="stop",
                        artifact=artifact_payload,
                    )
                    yield f"data: {payload.model_dump_json()} \n\n"
                else:
                    # No artifact - send a final message_chunk with finishReason="stop"
                    payload = ChunkMessage(
                        content="",
                        args={},
                        name="agent",
                        type="message_chunk",
                        id=str(final_msg_id),
                        finishReason="stop",
                    )
                    yield f"data: {payload.model_dump_json()} \n\n"
            except Exception as e:
                print(f"Error handling artifact: {e}")
                # Fallback - send stop message if error
                payload = ChunkMessage(
                    content="", args={}, name="agent", type="message_chunk", id=str(final_msg_id), finishReason="stop"
                )
                yield f"data: {payload.model_dump_json()} \n\n"

        # End of stream - save history
        end_time = datetime.datetime.now(datetime.timezone.utc)
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Stream finished, execution_time={execution_time}s")

        state = graph.get_state(config)
        prompt_token = state.values.get("prompt_token", 0)
        completion_token = state.values.get("completion_token", 0)
        total_token = prompt_token + completion_token
        logger.info(f"Token usage - prompt: {prompt_token}, completion: {completion_token}, total: {total_token}")

        if manager:
            try:
                # check if no tools is used
                if "tool_calls_name" not in locals():
                    tool_calls_name = None
                if "tool_calls_args" not in locals():
                    tool_calls_args = None
                if "tool_calls_id" not in locals():
                    tool_calls_id = None
                if "tool_calls_type" not in locals():
                    tool_calls_type = None

                decimal_execution_time = Decimal(str(execution_time)) if execution_time is not None else None
                manager.save_chat_history(
                    conversation_id=conversation_id,
                    user_input=message,
                    prompt_token=prompt_token,
                    completion_token=completion_token,
                    total_token=total_token,
                    end_time=end_time,
                    start_time=start_time,
                    execution_time=decimal_execution_time,
                    language=history_lang if history_lang else None,
                    tool_call_name=tool_calls_name if tool_calls_name else None,
                    tool_call_args=history_tool_args or tool_calls_args if tool_calls_args else None,
                    tool_call_id=tool_calls_id if tool_calls_id else None,
                    tool_call_type=tool_calls_type if tool_calls_type else None,
                    response=assistant_response,
                    category_id=metadata_history.get("id") if metadata_history else None,
                    category_name=metadata_history.get("name") if metadata_history else None,
                    source=artifact,
                )
                logger.info("Chat history saved successfully")
            except Exception as save_exc:
                logger.error("Error saving chat history to DynamoDB", exc_info=save_exc)
        else:
            logger.warning("DynamoDB not initialized; skipping save to history.")
    except Exception as exc:
        logger.error("Error in event_stream", exc_info=exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/streaming-answer")
async def stream(user_inputs: UserInputs):
    # Initialize exception handler for endpoint
    exception_handler = ExceptionHandler(
        logger=logger,
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.RAG,
    )
    try:
        logger.info(f"Received /stream request: conversation_id={user_inputs.conversation_id}")
        config = {"configurable": {"thread_id": user_inputs.conversation_id}}
        return StreamingResponse(event_stream(user_inputs, config), media_type="text/event-stream")
    except Exception as exc:
        # Handle errors when initiating stream
        logger.error("Error in stream endpoint", exc_info=exc)
        return exception_handler.handle_exception(e=str(exc), extra={"user_inputs": user_inputs.model_dump()})
