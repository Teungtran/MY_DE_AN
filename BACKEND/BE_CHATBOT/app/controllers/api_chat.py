import datetime
import asyncio
from typing_extensions import AsyncGenerator
import json
from decimal import Decimal
from schemas.chunk_message import ChunkMessage
from typing import Dict
from fastapi import APIRouter, HTTPException,Request,Depends
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langdetect import detect
from orchestrator.graph.main_graph import setup_agentic_graph
from orchestrator.graph.tools.support_nodes import format_message,extract_content_from_response
from sse_starlette.sse import EventSourceResponse
from utils.logging.logger import get_logger
from utils.token_counter import tiktoken_counter
from config.base_config import APP_CONFIG
from services.dynamodb import DynamoHistory
from services.redis_caching import redis_caching
from schemas.user_inputs import UserInputs,AuthenticatedUserInputs
from .login_page import get_current_user
from pydantic import EmailStr
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
logger = get_logger(__name__)

router = APIRouter()

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
redis_connect = redis_caching()

# Initialize graph with debug logging
logger.info("Initializing global graph instance...")
graph = setup_agentic_graph()
logger.info("Global graph instance initialized")

async def stream_and_save_response(conversation_id: str, user_id: str, user_message: str, 
                                final_response, final_tool_call, prompt_token: int, 
                                completion_token: int, start_time, history_lang: str,
                                tool_call_name, tool_call_args, tool_call_id, tool_call_type):
    """Helper function to stream response and save to database."""
    content = extract_content_from_response(final_response)
    await save_message_to_redis(conversation_id, "ai", content)
    
    chunk_size = 15
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i+chunk_size]
        print(chunk, end="|")
        payload = ChunkMessage(
            response=chunk,
            tools=[final_tool_call] if final_tool_call else None,
            prompt_token=prompt_token,
            completion_token=completion_token
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

async def save_message_to_redis(conversation_id: str, role: str, message: str):
    if not conversation_id or not redis_connect:
        logger.warning("Redis not available or no conversation_id, skipping message save")
        return
    
    message_data = {"role": role, "content": message}
    message_json = json.dumps(message_data)
    try:
        await asyncio.to_thread(redis_connect.rpush, f"chat:{conversation_id}", message_json)
        await asyncio.to_thread(redis_connect.ltrim, f"chat:{conversation_id}", -100, -1)
        await asyncio.to_thread(redis_connect.expire, f"chat:{conversation_id}", 86400)  
        await publish_to_channel(f"chat:{conversation_id}", message_data)
    except Exception as e:
        logger.error(f"Error saving message to Redis: {str(e)}")
##_______________________SETUP SSE____________________________________
async def retrieve_events(request: Request, conversation_id: str) -> AsyncGenerator[str, None]:
    pubsub = None
    try:
        if not redis_connect:
            logger.error("Redis not available for SSE")
            yield json.dumps({"error": "Chat history service unavailable"})
            return
            
        pubsub = redis_connect.pubsub()
        await asyncio.to_thread(pubsub.subscribe, f"chat:{conversation_id}")
        
        # Send existing chat history first
        try:
            history = await asyncio.to_thread(redis_connect.lrange, f"chat:{conversation_id}", 0, -1)
            for msg in history:
                msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else msg
                try:
                    message_data = json.loads(msg_str)
                    yield f"{json.dumps(message_data)}\n\n"
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON in history: {msg_str}")
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
        
        # Listen for new messages
        while not await request.is_disconnected():
            try:
                message = await asyncio.to_thread(pubsub.get_message, timeout=1.0, ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    yield f"{data}\n\n"
            except Exception as e:
                logger.error(f"Error in SSE message loop: {e}")
                break
    
    except asyncio.CancelledError:
        logger.info(f"SSE connection for conversation {conversation_id} was cancelled")
    except Exception as e:
        logger.error(f"Error in SSE connection: {e}")
        yield f"{json.dumps({'error': str(e)})}\n\n"
    finally:
        if pubsub:
            try:
                await asyncio.to_thread(pubsub.unsubscribe, f"chat:{conversation_id}")
                await asyncio.to_thread(pubsub.close)
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")

@router.get("/{conversation_id}/subscribe")
async def subscribe_to_stream(request: Request, conversation_id: str):
    return EventSourceResponse(retrieve_events(request, conversation_id))

@router.get("/{conversation_id}/messages")
async def get_chat_history(conversation_id: str):
    try:
        if not redis_connect:
            logger.warning("Redis not available, returning empty history")
            return []
            
        exists = await asyncio.to_thread(redis_connect.exists, f"chat:{conversation_id}")
        if exists:
            history = await asyncio.to_thread(redis_connect.lrange, f"chat:{conversation_id}", 0, -1)
            messages = []
            for msg in history:
                try:
                    msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else msg
                    message_data = json.loads(msg_str)
                    messages.append(message_data)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON in history: {msg}")
            return messages
        return []
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
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

        # Log initial graph state
        logger.debug(f"Initial graph state for conversation {conversation_id}:")
        initial_snapshot = graph.get_state(config)
        if isinstance(initial_snapshot, tuple):
            initial_snapshot = initial_snapshot[0]
        logger.debug(f"Initial snapshot: {initial_snapshot}")
        
        user_message = user_inputs.message
        await save_message_to_redis(conversation_id, "human", user_message) 
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
                
                if user_message.strip().lower() == "y":
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
                    confirmation_message = (
                        f"Please confirm your request: {tool_args}, press 'y' to confirm or 'n' to reject.\n"
                        f"Vui lòng xác nhận yêu cầu: {tool_args}, nhấn 'y' để xác nhận hoặc 'n' để từ chối."
                    )
                    await save_message_to_redis(conversation_id, "ai", confirmation_message)
                    for char in confirmation_message:
                        print(char, end="|")
                        payload = ChunkMessage(
                            response=char,
                            tools=None,
                            prompt_token=0,
                            completion_token=0
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
            tools=None
        )
        yield f"{error_payload.model_dump_json()}\n\n"

@router.post("/streaming-answer")
async def stream(
    user_inputs: UserInputs,
    current_user: dict = Depends(get_current_user)
):
    """Stream AI response with authentication"""
    exception_handler = ExceptionHandler(
        logger=logger,
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.WORKFLOWs,
    )
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
