import datetime
import asyncio
from typing_extensions import AsyncGenerator
import json
from decimal import Decimal
from app.schemas.chunk_message import ChunkMessage
from typing import Dict
from fastapi import APIRouter, HTTPException,Request,Depends
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langdetect import detect
from app.orchestrator.graph.main_graph import setup_agentic_graph
from app.orchestrator.graph.tools.support_nodes import format_message,extract_content_from_response
from sse_starlette.sse import EventSourceResponse
from app.utils.logging.logger import get_logger
from app.utils.token_counter import tiktoken_counter
from app.config.base_config import APP_CONFIG
from app.services.dynamodb import DynamoHistory
from app.services.redis_caching import redis_caching
from app.schemas.user_inputs import UserInputs,AuthenticatedUserInputs
from app.controllers.login_page import require_user_role
from pydantic import EmailStr
from app.utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
logger = get_logger(__name__)
from app.factories.chat_factory import create_chat_model

router = APIRouter()
chat_config = APP_CONFIG.chat_model_config

# DynamoDB config
AWS_SECRET_ACCESS_KEY = APP_CONFIG.dynamo_config.aws_secret_access_key
TABLE_NAME = APP_CONFIG.dynamo_config.table_name
AWS_SECRET_ACCESS_ID = APP_CONFIG.dynamo_config.aws_access_key_id
REGION_NAME = APP_CONFIG.dynamo_config.region_name

def initialize_dynamo():
    global manager
    try:
        table_name = TABLE_NAME
        if callable(TABLE_NAME):
            try:
                table_name = TABLE_NAME()
            except:
                table_name = "CHAT_HISTORY"
                logger.warning(f"Could not call table name function, using default: {table_name}")
        
        logger.info(f"DynamoDB config - TABLE: {table_name}, REGION: {REGION_NAME}")
        
        manager = DynamoHistory(
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_SECRET_ACCESS_ID,
            table_name=table_name,
            region_name=REGION_NAME,
        )
        logger.info("DynamoHistory initialized successfully")
    except Exception as init_exc:
        logger.error("Error initializing DynamoHistory", exc_info=init_exc)
        manager = None
        



initialize_dynamo()
logger.info("Initializing Redis connection for chatbot service...")
redis_connect = redis_caching()
if redis_connect:
    logger.info("Redis connection initialized successfully for chatbot service")
else:
    logger.warning("Redis connection initialization failed for chatbot service - some features may be unavailable")

# Initialize graph with debug logging
logger.info("Initializing global graph instance...")
graph = setup_agentic_graph()
logger.info("Global graph instance initialized")

# ---------------- UI title cache per conversation -----------------
_ui_title_cache: Dict[str, str] = {}

llm = create_chat_model(chat_config)
prompt = """
give the intention of the given message in less than 5 words
"""

def _get_ui_title_for_session(session_id: str, message: str) -> str:
    """Return cached ui title for session, computing once if missing."""
    if session_id in _ui_title_cache:
        return _ui_title_cache[session_id]
    title_response = llm.invoke(prompt + message)
    # Extract content from AIMessage object
    title = title_response.content if hasattr(title_response, 'content') else str(title_response)
    _ui_title_cache[session_id] = title
    return title

def format_tool_args_to_markdown(tool_args: dict) -> str:
    """
    Convert tool arguments dictionary to a readable markdown format.
    Dynamically formats any dictionary without hardcoded field mappings.
    
    Args:
        tool_args: Dictionary containing tool call arguments
        
    Returns:
        Formatted markdown string with proper labels and values
    """
    if not tool_args or not isinstance(tool_args, dict):
        return str(tool_args)
    
    formatted_lines = []
    for key, value in tool_args.items():
        # Convert snake_case to Title Case for readability
        readable_key = key.replace('_', ' ').title()
        # Add newline at the end of each line to ensure proper line breaks
        formatted_lines.append(f"• **{readable_key}**: {value}\n")
    
    # Join lines (each already has \n at the end)
    return ''.join(formatted_lines)

async def stream_and_save_response(conversation_id: str, user_id: str, user_message: str, 
                            final_response, final_tool_call, prompt_token: int, 
                            completion_token: int, start_time, history_lang: str,
                            tool_call_name, tool_call_args, tool_call_id, tool_call_type):
    """Helper function to stream response and save to database."""
    content = extract_content_from_response(final_response)
    await save_message_to_redis(conversation_id, "ai", content, user_id)
    
    chunk_size = 15
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i+chunk_size]
        print(chunk, end="|")
        payload = ChunkMessage(
            response=chunk,
            tools=[final_tool_call] if final_tool_call else None,
            prompt_token=prompt_token,
            completion_token=completion_token,
            title=_get_ui_title_for_session(conversation_id, user_message),
            conversation_id=conversation_id
        )
        yield f"{payload.model_dump_json()}\n\n"
    
    # Log and save to database after streaming is complete
    end_time = datetime.datetime.now(datetime.timezone.utc)
    execution_time = (end_time - start_time).total_seconds()
    logger.info(f"Stream finished, execution_time={execution_time}s")
    
    if manager:  # Always save if manager exists, regardless of final_response
        try:
            decimal_execution_time = Decimal(str(execution_time)) if execution_time is not None else None
            response_content = extract_content_from_response(final_response) if final_response else None
            
            manager.save_chat_history(
                conversation_id=conversation_id,
                user_id=user_id,
                user_input=user_message,
                prompt_token=prompt_token,
                completion_token=completion_token,
                total_token=prompt_token+completion_token,
                end_time=end_time,
                start_time=start_time,
                execution_time=decimal_execution_time,
                language=history_lang,
                tool_call_name=final_tool_call['name'] if final_tool_call else tool_call_name,
                tool_call_args=final_tool_call['args'] if final_tool_call else tool_call_args,
                tool_call_id=final_tool_call['id'] if final_tool_call else tool_call_id,
                tool_call_type=final_tool_call['type'] if final_tool_call else tool_call_type,
                response=response_content
            )
            logger.info("Chat history saved successfully")
        except Exception as save_exc:
            logger.error("Error saving chat history to DynamoDB", exc_info=save_exc)
    else:
        logger.warning("DynamoDB manager not available; skipping save to history.")

#_____________________SETUP CACHING______________________________
async def publish_to_channel(channel: str, message: dict):
    if not redis_connect:
        logger.warning("Redis not available, skipping channel publish")
        return
    try:
        message_json = json.dumps(message)
        await asyncio.to_thread(redis_connect.publish, channel, message_json)
    except Exception as e:
        logger.error(f"Error publishing to channel {channel}: {str(e)}")

async def save_message_to_redis(conversation_id: str, role: str, message: str, user_id: str = None):
    if not conversation_id or not redis_connect:
        logger.warning("Redis not available or no conversation_id, skipping message save")
        return
    
    message_data = {"role": role, "content": message}
    message_json = json.dumps(message_data)
    try:
        await asyncio.to_thread(redis_connect.rpush, f"chat:{conversation_id}", message_json)
        await asyncio.to_thread(redis_connect.ltrim, f"chat:{conversation_id}", -100, -1)
        await asyncio.to_thread(redis_connect.expire, f"chat:{conversation_id}", 86400)
        
        # Store user_id mapping to track all conversations per user
        if user_id:
            # Add conversation_id to user's conversation set
            await asyncio.to_thread(redis_connect.sadd, f"user:{user_id}:conversations", conversation_id)
            await asyncio.to_thread(redis_connect.expire, f"user:{user_id}:conversations", 86400)
            # Store user_id for conversation (for reverse lookup/verification)
            await asyncio.to_thread(redis_connect.set, f"conversation:{conversation_id}:user_id", user_id, ex=86400)
        
        await publish_to_channel(f"chat:{conversation_id}", message_data)
    except Exception as e:
        logger.error(f"Error saving message to Redis: {str(e)}")


@router.get("/messages")
async def get_chat_history(
    current_user: dict = Depends(require_user_role)
):
    """Get all chat histories for the authenticated user"""
    try:
        if not redis_connect:
            logger.warning("Redis not available, returning empty history")
            return {}
        
        user_id = current_user['user_id']
        
        # Get all conversation_ids for this user
        conversation_ids = await asyncio.to_thread(
            redis_connect.smembers, 
            f"user:{user_id}:conversations"
        )
        
        # Convert bytes to strings if needed
        conversation_ids = [
            conv_id.decode('utf-8') if isinstance(conv_id, bytes) else conv_id 
            for conv_id in conversation_ids
        ]
        
        if not conversation_ids:
            logger.info(f"No conversations found for user_id={user_id}")
            return {}
        
        # Get history for each conversation
        all_conversations = {}
        logger.info(f"Retrieving chat history for user_id={user_id}, found {len(conversation_ids)} conversation_ids")
        
        for conv_id in conversation_ids:
            try:
                # Verify conversation belongs to user (security check)
                stored_user_id = await asyncio.to_thread(
                    redis_connect.get, 
                    f"conversation:{conv_id}:user_id"
                )
                
                if stored_user_id:
                    stored_user_id = stored_user_id.decode('utf-8') if isinstance(stored_user_id, bytes) else stored_user_id
                    if stored_user_id != user_id:
                        logger.warning(f"Conversation {conv_id} does not belong to user {user_id} (belongs to {stored_user_id}), skipping")
                        continue
                else:
                    # If no user_id stored, log but still include it (might be old data)
                    logger.debug(f"Conversation {conv_id} has no stored user_id, but is in user's conversation set - including it")
                
                # Get messages for this conversation
                exists = await asyncio.to_thread(redis_connect.exists, f"chat:{conv_id}")
                if exists:
                    history = await asyncio.to_thread(redis_connect.lrange, f"chat:{conv_id}", 0, -1)
                    messages = []
                    for msg in history:
                        try:
                            msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else msg
                            message_data = json.loads(msg_str)
                            messages.append(message_data)
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping invalid JSON in history for conversation {conv_id}: {msg}")
                    
                    # Include conversation even if empty (to show all conversations)
                    all_conversations[conv_id] = messages
                    logger.debug(f"Retrieved {len(messages)} messages for conversation {conv_id}")
                else:
                    # Conversation exists in user's set but has no messages - include as empty
                    logger.debug(f"Conversation {conv_id} exists in user's set but has no messages - including as empty")
                    all_conversations[conv_id] = []
            except Exception as e:
                logger.error(f"Error retrieving conversation {conv_id} for user {user_id}: {str(e)}")
                # Continue processing other conversations even if one fails
                continue
        
        logger.info(f"Returning {len(all_conversations)} conversations for user_id={user_id}")
        return all_conversations
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}, user_id={current_user['user_id']}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")



async def stream_event(user_inputs: UserInputs, config: Dict, user_id:str,email:EmailStr) -> AsyncGenerator[str, None]:
    """
    Send a message to the FPT Shop Assistant with a given thread_id,
    return only the final AI response and the final tool call.
    Handles both regular messages and tool call confirmations.
    """
    try:
        start_time = datetime.datetime.now(datetime.timezone.utc)
        conversation_id = user_inputs.conversation_id
        logger.info(f"Starting event_stream: conversation_id={conversation_id}")
        # Ensure UI title is generated only once per conversation
        _ = _get_ui_title_for_session(conversation_id, user_inputs.message)

        # Log initial graph state
        logger.debug(f"Initial graph state for conversation {conversation_id}:")
        initial_snapshot = graph.get_state(config)
        if isinstance(initial_snapshot, tuple):
            initial_snapshot = initial_snapshot[0]
        logger.debug(f"Initial snapshot: {initial_snapshot}")
        
        user_message = user_inputs.message
        await save_message_to_redis(conversation_id, "human", user_message, user_id) 
        tool_call_name = None
        tool_call_args = None
        tool_call_id = None
        tool_call_type = None
        history_lang = detect(user_message) if user_message else None
        
        initial_chat_history = initial_snapshot.get("messages", []) if hasattr(initial_snapshot, 'get') else []
        initial_prompt_token = tiktoken_counter(initial_chat_history) if initial_chat_history else 0
        logger.debug(f"Initial chat history length: {len(initial_chat_history)}")

        snapshot = graph.get_state(config)
        logger.debug(f"State before processing for {conversation_id}: {snapshot}")
        
        if snapshot and snapshot.next:
            logger.debug(f"Found pending state for {conversation_id}")
            last_toolcall_message = None
            
            if hasattr(snapshot, 'values') and "messages" in snapshot.values:
                last_message = snapshot.values["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    last_toolcall_message = last_message
                    logger.debug(f"Found pending tool call: {last_toolcall_message.tool_calls}")
            
            if last_toolcall_message:
                logger.debug(f"Processing pending tool call for {conversation_id}")
                processed_set = set()
                all_messages = []
                all_tool_calls = []
                
                confirmation_inputs = {"y", "yes", "ok", "confirm", "đồng ý", "dong y"}
                if user_message.strip().lower() in confirmation_inputs:
                    logger.debug("User confirmed tool call")
                    result = graph.invoke(None, config)
                else:
                    logger.debug("User rejected tool call")
                    tool_call_id = last_toolcall_message.tool_calls[0]["id"]
                    result = graph.invoke(
                        {
                            "messages": [
                                ToolMessage(
                                    tool_call_id=tool_call_id,
                                    content=f"API call denied by user. Reasoning: '{user_message}'. Continue assisting, accounting for the user's input.",
                                )
                            ]
                        },
                        config,
                    )
                
                logger.debug(f"Tool call result: {result}")
                
                if "messages" in result:
                    for msg in result["messages"]:
                        msg_content = format_message(msg)
                        msg_hash = hash(msg_content)
                        if msg_hash not in processed_set:
                            processed_set.add(msg_hash)
                            all_messages.append({
                                "content": msg_content,
                                "message": msg
                            })
                            
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    all_tool_calls.append({
                                        "name": tool_call['name'],
                                        "args": tool_call.get('args', {}),
                                        "id": tool_call['id'],
                                        "type": tool_call['type']
                                    })
                
                # Get final response from processed messages
                final_response = ""
                for msg_data in reversed(all_messages):
                    content = msg_data["content"]
                    message = msg_data["message"]
                    message_type = type(message).__name__
                    
                    if (message_type == "AIMessage" and 
                        content and 
                        content.strip() and 
                        not content.startswith("content=''") and
                        not content.startswith("The assistant is now")):
                        
                        final_response = content
                        break
                
                final_tool_call = all_tool_calls[-1] if all_tool_calls else None
                completion_token = tiktoken_counter([AIMessage(content=final_response)])
                
                snapshot = graph.get_state(config)
                if isinstance(snapshot, tuple):
                    snapshot = snapshot[0]
                
                chat_history = snapshot.get("messages", []) if hasattr(snapshot, 'get') else []
                total_prompt_token = tiktoken_counter(chat_history) if chat_history else 0
                prompt_token = total_prompt_token - initial_prompt_token
                
                logger.debug(f"Final state after tool call processing: {snapshot}")
                
                async for chunk in stream_and_save_response(
                    conversation_id, user_id, user_message, final_response, 
                    final_tool_call, prompt_token, completion_token, start_time, 
                    history_lang, tool_call_name, tool_call_args, tool_call_id, tool_call_type
                ):
                    yield chunk
                
                return  
        
        logger.debug(f"Starting new conversation for {conversation_id}")
        processed_set = set()
        all_messages = []
        all_tool_calls = []
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "conversation_id": conversation_id,
            "user_id": user_id,
            "email": email,
            "dialog_state": ["primary_assistant"],
            "recommended_devices": []
        }
        logger.debug(f"Initial state for new conversation: {initial_state}")
        
        events = graph.stream(
            initial_state,
            config,
            stream_mode="values"
        )

        for event in events:
            if "messages" in event:
                for message in event["messages"]:
                    msg_content = format_message(message)
                    msg_hash = hash(msg_content)
                    if msg_hash not in processed_set:
                        processed_set.add(msg_hash)
                        all_messages.append({
                            "content": msg_content,
                            "message": message
                        })
                        
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            for tool_call in message.tool_calls:
                                all_tool_calls.append({
                                    "name": tool_call['name'],
                                    "args": tool_call.get('args', {}),
                                    "id": tool_call['id'],
                                    "type": tool_call['type']
                                })

        snapshot = graph.get_state(config)
        logger.debug(f"State after processing for {conversation_id}: {snapshot}")
        
        if snapshot and snapshot.next:
            if hasattr(snapshot, 'values') and "messages" in snapshot.values:
                last_message = snapshot.values["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    tool_args = last_message.tool_calls[0]["args"]
                    logger.debug(f"New tool call request: {tool_args}")
                    
                    # Remove user_id from tool_args before formatting
                    args_to_display = {k: v for k, v in tool_args.items() if k != "user_id"}
                    
                    # Format tool args to markdown (without user_id)
                    formatted_args = format_tool_args_to_markdown(args_to_display)

                    confirmation_message = (
                        f"**Please confirm your request / Vui lòng xác nhận yêu cầu:**\n\n"
                        f"{formatted_args}\n\n"
                        f"Press **'y'** to confirm / Nhấn **'y'** để xác nhận\n"
                        f"Press **'n'** to reject / Nhấn **'n'** để từ chối"
                    )
                    await save_message_to_redis(conversation_id, "ai", confirmation_message, user_id)
                    for char in confirmation_message:
                        print(char, end="|")
                        payload = ChunkMessage(
                            response=char,
                            tools=None,
                            prompt_token=0,
                            completion_token=0,
                            title=_get_ui_title_for_session(conversation_id, user_message),
                            conversation_id=conversation_id
                        )
                        yield f"{payload.model_dump_json()}\n\n"
                    return

        # Get final response
        final_response = ""
        for msg_data in reversed(all_messages):
            content = msg_data["content"]
            message = msg_data["message"]
            message_type = type(message).__name__
            
            if (message_type == "AIMessage" and 
                content and 
                content.strip() and 
                not content.startswith("content=''") and
                not content.startswith("The assistant is now")):
                
                final_response = content
                break

        final_tool_call = all_tool_calls[-1] if all_tool_calls else None
        completion_token = tiktoken_counter([AIMessage(content=final_response)])

        snapshot = graph.get_state(config)
        if isinstance(snapshot, tuple):
            snapshot = snapshot[0]
        chat_history = snapshot.get("messages", []) if hasattr(snapshot, 'get') else []
        total_prompt_token = tiktoken_counter(chat_history) if chat_history else 0
        prompt_token = total_prompt_token - initial_prompt_token
        
        logger.debug(f"Final state after conversation: {snapshot}")
        
        async for chunk in stream_and_save_response(
            conversation_id, user_id, user_message, final_response, 
            final_tool_call, prompt_token, completion_token, start_time, 
            history_lang, tool_call_name, tool_call_args, tool_call_id, tool_call_type
        ):
            yield chunk
                
    except Exception as exc:
        logger.error("Error in event_stream", exc_info=exc)
        error_payload = ChunkMessage(
            response=f"An error occurred: {str(exc)}",
            prompt_token=0,
            completion_token=0,
            tools=None,
            title=_get_ui_title_for_session(user_inputs.conversation_id, user_inputs.message) if user_inputs and user_inputs.conversation_id else None,
            conversation_id=user_inputs.conversation_id if user_inputs else None
        )
        yield f"{error_payload.model_dump_json()}\n\n"

@router.post("/streaming-answer")
async def stream(
    user_inputs: UserInputs,
    current_user: dict = Depends(require_user_role)
):
    """Stream AI response with authentication"""
    exception_handler = ExceptionHandler(
        logger=logger,
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.WORKFLOWs,
    )
    # Mock user for testing (commented out - use for future tests if needed)
    # mock_user_id = "test_user_123"
    # mock_email = "test@example.com"
    
    try:
        logger.info(f"Received /stream request: conversation_id={user_inputs.conversation_id}, user_id={current_user['user_id']}")
        
        # Create authenticated user inputs
        authenticated_inputs = AuthenticatedUserInputs(
            conversation_id=user_inputs.conversation_id,
            message=user_inputs.message,
            user_id=current_user['user_id'],
            email=current_user['email']
        )
        
        config = {
            "configurable": {"thread_id": user_inputs.conversation_id},
            "user_id": current_user['user_id'],
            "email": current_user['email'],
            "recursion_limit": 50
        }
        
        return EventSourceResponse(
            stream_event(
                user_inputs=authenticated_inputs, 
                config=config, 
                user_id=current_user['user_id'],
                email=current_user['email']
            )
        )
    except Exception as exc:
        logger.error("Error in stream endpoint", exc_info=exc)
        return exception_handler.handle_exception(
            e=str(exc), 
            extra={"user_inputs": user_inputs.model_dump(), "user_id": current_user['user_id']}
        )
