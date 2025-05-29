import datetime
from decimal import Decimal
from schemas.chunk_message import ChunkMessage
from typing import Optional, Dict, Any, Union, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langdetect import detect, LangDetectException
from orchestrator.graph.main_graph import setup_agentic_graph
from orchestrator.graph.tools.support_nodes import format_message

from utils.logging.logger import get_logger
from utils.token_counter import tiktoken_counter
from config.base_config import APP_CONFIG
from services.dynamodb import DynamoHistory
from schemas.user_inputs import UserInputs
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName

logger = get_logger(__name__)

router = APIRouter()

# DynamoDB config
AWS_SECRET_ACCESS_KEY = APP_CONFIG.dynamo_config.aws_secret_access_key
TABLE_NAME = APP_CONFIG.dynamo_config.table_name
AWS_SECRET_ACCESS_ID = APP_CONFIG.dynamo_config.aws_access_key_id
REGION_NAME = APP_CONFIG.dynamo_config.region_name

manager: Optional[DynamoHistory] = None

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

async def event_stream(user_inputs: UserInputs, config: Dict) -> AsyncGenerator[tuple, None]:
    """
    Stream responses following the test_fpt_shop_assistant logic but with streaming
    """
    try:
        start_time = datetime.datetime.now(datetime.timezone.utc)
        conversation_id = user_inputs.conversation_id
        user_id = user_inputs.user_id
        logger.info(f"Starting event_stream: conversation_id={conversation_id}")
        user_message = user_inputs.message
        tool_call_name = None
        tool_call_args = None
        tool_call_id = None
        tool_call_type = None
        history_lang = None
        prompt_token = 0
        completion_token = 0
        
        # Safe language detection
        try:
            history_lang = detect(user_message) if user_message else None
        except LangDetectException:
            history_lang = None
            logger.warning("Could not detect language for user message")
            
        graph = setup_agentic_graph()
        initial_snapshot = graph.get_state(config)
        if isinstance(initial_snapshot, tuple):
            initial_snapshot = initial_snapshot[0]
        initial_chat_history = initial_snapshot.get("messages", []) if hasattr(initial_snapshot, 'get') else []
        initial_prompt_token = tiktoken_counter(initial_chat_history) if initial_chat_history else 0
        snapshot = graph.get_state(config)
        if snapshot and snapshot.next:
            last_toolcall_message = None
            
            if hasattr(snapshot, 'values') and "messages" in snapshot.values:
                last_message = snapshot.values["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    last_toolcall_message = last_message
            
            if last_toolcall_message:
                processed_set = set()
                all_messages = []
                all_tool_calls = []
                
                if user_message.strip().lower() == "y":
                    result = graph.invoke(None, config)
                else:
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
                
                # Process the result
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
                prompt_token = tiktoken_counter(chat_history) if chat_history else 0
                
                # Stream the response
                if final_response:
                    yield final_response, None, prompt_token, completion_token
                
                # Save to history and return
                await save_chat_history(
                    manager, conversation_id, user_message, prompt_token, 
                    completion_token, start_time, history_lang, 
                    final_tool_call, tool_call_name, tool_call_args, 
                    tool_call_id, tool_call_type, final_response
                )
                return
        
        # Normal flow - process new message
        processed_set = set()
        all_messages = []
        all_tool_calls = []
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "conversation_id": conversation_id,  
            "dialog_state": ["primary_assistant"]
        }
        
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

        # Check if there's a pending tool call that needs confirmation
        snapshot = graph.get_state(config)
        if snapshot and snapshot.next:
            if hasattr(snapshot, 'values') and "messages" in snapshot.values:
                last_message = snapshot.values["messages"][-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    tool_args = last_message.tool_calls[0]["args"]
                    confirmation_message = (
                        f"Please confirm your request: {tool_args}, press 'y' to confirm or 'n' to reject.\n"
                        f"Vui lòng xác nhận yêu cầu: {tool_args}, nhấn 'y' để xác nhận hoặc 'n' để từ chối."
                    )
                    yield confirmation_message, None, 0, 0
                    return

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
        completion_token = tiktoken_counter([AIMessage(content=final_response)]) if final_response else 0

        snapshot = graph.get_state(config)
        if isinstance(snapshot, tuple):
            snapshot = snapshot[0]
        chat_history = snapshot.get("messages", []) if hasattr(snapshot, 'get') else []
        total_prompt_token = tiktoken_counter(chat_history) if chat_history else 0
        prompt_token = total_prompt_token - initial_prompt_token

        end_time = datetime.datetime.now(datetime.timezone.utc)
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Stream finished, execution_time={execution_time}s")
        
        total_token = prompt_token + completion_token
        logger.info(f"Token usage - prompt: {prompt_token}, completion: {completion_token}, total: {total_token}")
        print(f"Token usage - prompt: {prompt_token}, completion: {completion_token}, total: {total_token}")
        
        # Stream the final response
        if final_response:
            yield final_response, final_tool_call, prompt_token, completion_token
        else:
            yield "No response generated", None, prompt_token, completion_token
        
        # Save chat history
        await save_chat_history(
            manager, user_id,conversation_id, user_message, prompt_token, 
            completion_token, start_time, history_lang, 
            final_tool_call, tool_call_name, tool_call_args, 
            tool_call_id, tool_call_type, final_response
        )
        
    except Exception as exc:
        logger.error("Error in event_stream", exc_info=exc)
        error_message = f"Error: {str(exc)}"
        yield error_message, None, 0, 0
        raise HTTPException(status_code=500, detail=str(exc))

async def save_chat_history(
    manager, user_id, conversation_id, user_message, prompt_token, 
    completion_token, start_time, history_lang, 
    final_tool_call, tool_call_name, tool_call_args, 
    tool_call_id, tool_call_type, final_response
):
    """Helper function to save chat history to DynamoDB"""
    if manager and final_response:
        try:
            end_time = datetime.datetime.now(datetime.timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            decimal_execution_time = Decimal(str(execution_time)) if execution_time is not None else None
            total_token = prompt_token + completion_token
            
            manager.save_chat_history(
                conversation_id=conversation_id,
                user_id=user_id,
                user_input=user_message,
                prompt_token=prompt_token,
                completion_token=completion_token,
                total_token=total_token,
                end_time=end_time,
                start_time=start_time,
                execution_time=decimal_execution_time,
                language=history_lang,
                tool_call_name=final_tool_call['name'] if final_tool_call else tool_call_name,
                tool_call_args=final_tool_call['args'] if final_tool_call else tool_call_args,
                tool_call_id=final_tool_call['id'] if final_tool_call else tool_call_id,
                tool_call_type=final_tool_call['type'] if final_tool_call else tool_call_type,
                response=final_response
            )
            logger.info("Chat history saved successfully")
        except Exception as save_exc:
            logger.error("Error saving chat history to DynamoDB", exc_info=save_exc)
    else:
        if not manager:
            logger.warning("DynamoDB not initialized; skipping save to history.")
        elif not final_response:
            logger.warning("No final response available; skipping save to history.")

async def format_stream_response(user_inputs: UserInputs, config: Dict) -> AsyncGenerator[str, None]:
    """
    Wrapper to format the tuple response from event_stream into strings for StreamingResponse
    """
    try:
        async for response_tuple in event_stream(user_inputs, config):
            message, tool_call, prompt_tokens, completion_tokens = response_tuple
            
            # Format as JSON string for structured response
            response_data = {
                "message": message,
                "tool_call": tool_call,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            
            # Convert to JSON string and add newline for streaming
            import json
            yield f"data: {json.dumps(response_data)}\n\n"
            
    except Exception as exc:
        logger.error("Error in format_stream_response", exc_info=exc)
        error_response = {
            "message": f"Error: {str(exc)}",
            "tool_call": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        import json
        yield f"data: {json.dumps(error_response)}\n\n"

@router.post("/streaming-answer")
async def stream(user_inputs: UserInputs):
    exception_handler = ExceptionHandler(
        logger=logger,
        service_name=ServiceName.ORCHESTRATOR,
        function_name=FunctionName.WORKFLOWs,
    )
    try:
        logger.info(f"Received /stream request: conversation_id={user_inputs.conversation_id}")
        config = {
            "configurable": {"thread_id": user_inputs.conversation_id},
            "recursion_limit": 10
        }
        return StreamingResponse(format_stream_response(user_inputs, config), media_type="text/event-stream")
    except Exception as exc:
        logger.error("Error in stream endpoint", exc_info=exc)
        return exception_handler.handle_exception(e=str(exc), extra={"user_inputs": user_inputs.model_dump()})