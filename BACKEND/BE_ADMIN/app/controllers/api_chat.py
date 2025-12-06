import datetime
import json 
from typing import Optional, Dict
import asyncio
import shutil
from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Query
from app.workflow.team_agents import store_team
from pydantic import BaseModel, Field
from app.controllers.login_page import require_store_role 
from app.report_agent.execute import trigger
from app.report_agent.main_agent import llm, clear_data_info_cache

from app.report_agent.parse_file import import_data
from app.report_agent.agent import clear_data_cache
from app.utils.logging.logger import get_logger
logger = get_logger(__name__)
import pandas as pd
from app.controllers.redis_caching import redis_caching
router = APIRouter()

class TeamChatRequest(BaseModel):
    """Schema for team chat requests"""
    message: str = Field(..., description="User message")

prompt = """
give the intention of the given message in less than 5 words
"""
redis_connect = redis_caching()

# Cache for per-session UI titles to ensure we compute it only once per session
_ui_title_cache: Dict[str, str] = {}

def _get_ui_title_for_session(session_id: str, message: str) -> str:
    """Return cached ui title for session, computing once if missing."""
    if session_id in _ui_title_cache:
        return _ui_title_cache[session_id]
    title_response = llm.invoke(prompt + message)
    title = title_response.content if hasattr(title_response, 'content') else str(title_response)
    _ui_title_cache[session_id] = title
    return title

async def publish_to_channel(channel: str, message: dict):
    if not redis_connect:
        logger.warning("Redis not available, skipping channel publish")
        return
    try:
        message_json = json.dumps(message)
        await asyncio.to_thread(redis_connect.publish, channel, message_json)
    except Exception as e:
        logger.error(f"Error publishing to channel {channel}: {str(e)}")

async def save_message_to_redis(id: str, role: str, message: str):
    if not id or not redis_connect:
        logger.warning("Redis not available or no id, skipping message save")
        return
    
    message_data = {"role": role, "content": message}
    message_json = json.dumps(message_data)
    try:
        await asyncio.to_thread(redis_connect.rpush, f"chat:{id}", message_json)
        await asyncio.to_thread(redis_connect.ltrim, f"chat:{id}", -100, -1)
        await asyncio.to_thread(redis_connect.expire, f"chat:{id}", 86400)  
        await publish_to_channel(f"chat:{id}", message_data)
    except Exception as e:
        logger.error(f"Error saving message to Redis: {str(e)}")

@router.get("/{id}/messages")
async def get_chat_history(id: str):
    try:
        if not redis_connect:
            logger.warning("Redis not available, returning empty history")
            return []
            
        exists = await asyncio.to_thread(redis_connect.exists, f"chat:{id}")
        if exists:
            history = await asyncio.to_thread(redis_connect.lrange, f"chat:{id}", 0, -1)
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
    
@router.post("/team/chat/stream")
async def stream_team_chat(
    request: TeamChatRequest,
    id: Optional[str] = Query(None, description="Session ID (optional, will generate new one if not provided)"),
    current_user: dict = Depends(require_store_role)
):
    """
    Get chat responses from the store team (requires admin/staff role)
    Returns the complete response content directly.
    """
    try:
        if id is None:
            id = str(uuid.uuid4())
        user_id = "id" #current_user["user_id"]
        logger.info(f"Starting team chat for user {user_id}, session {id}")
        ui_message = _get_ui_title_for_session(id, request.message)
        await save_message_to_redis(id, "human", request.message) 

        # Run the store team
        result = store_team.run(
            session_id=id,
            user_id=user_id,
            message=request.message,
            stream=False
        )
        
        # Extract content from result
        complete_ai_response = ""
        try:
            if hasattr(result, 'content'):
                complete_ai_response = result.content or ""
            else:
                complete_ai_response = str(result) if result is not None else ""
        except Exception as e:
            logger.warning(f"Error extracting content from result: {e}")
            complete_ai_response = str(result) if result is not None else ""
        
        # Ensure it's a string
        if not isinstance(complete_ai_response, str):
            complete_ai_response = str(complete_ai_response)
        
        # Save to Redis
        if complete_ai_response:
            await save_message_to_redis(id, "ai", complete_ai_response)
        
        # Return response directly
        return {
            "content": complete_ai_response,
            "title": ui_message,
            "session_id": id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process team chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


# Report Analysis Endpoints
@router.post("/report/upload")
async def upload_file(
    file: UploadFile = File(...),
    # current_user: dict = Depends(require_store_role)
):
    """Upload report file for analysis (requires admin/staff role)"""
    # Mock user for testing (commented out - use for future tests if needed)
    mock_user_id = "test_user"
    
    # Validate file exists
    if not file or not file.filename:
        logger.error("No file provided in upload request")
        raise HTTPException(status_code=400, detail="No file provided")
    
    allowed_extensions = {'.csv', '.xlsx', '.xls'}
    file_extension = Path(file.filename).suffix.lower()
    
    logger.info(f"Uploading file: {file.filename}, extension: {file_extension}")
    
    if file_extension not in allowed_extensions:
        logger.error(f"Unsupported file type: {file_extension}")
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Use the same path resolution as parse_file.py
    # From api_chat.py (app/controllers/) -> go up to app/ -> then to report_agent/artifact
    artifact_dir = Path(__file__).parent.parent / "report_agent" / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Artifact directory: {artifact_dir.absolute()}")
    
    supported_extensions = ['.csv', '.txt', '.xlsx', '.xls']
    existing_files = [f for f in artifact_dir.iterdir() if f.suffix.lower() in supported_extensions]
    
    for existing_file in existing_files:
        try:
            existing_file.unlink()  
            logger.info(f"Deleted old file: {existing_file.name}")
        except Exception as e:
            logger.warning(f"Could not delete {existing_file.name}: {e}")
    
    # Save the new file
    file_path = artifact_dir / file.filename
    logger.info(f"Saving file to: {file_path.absolute()}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Verify file was saved
    if not file_path.exists():
        logger.error(f"File was not saved successfully to {file_path.absolute()}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    logger.info(f"File saved successfully: {file_path.name}, size: {file_path.stat().st_size} bytes")
    
    # Clear data caches since new file was uploaded
    clear_data_cache()
    clear_data_info_cache()
    logger.info("Data caches cleared after new file upload")
    
    try:
        df = import_data()  
        
        df = df.where(pd.notnull(df), None)
        data_records = df.to_dict(orient="records")
        logger.info(f"File uploaded and parsed successfully: {file.filename}, {len(data_records)} records")
    except ValueError as e:
        logger.error(f"ValueError parsing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error parsing file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")

    return {"filename": file.filename, "data": data_records}

@router.post("/report/analyze")
async def report_agent(
    question: str = Form(...),
    # current_user: dict = Depends(require_store_role)
):
    """Analyze uploaded data file with a natural language question (requires admin/staff role)
    Returns the complete analysis content directly.
    """
    try:
        content = trigger(question)
        
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content) if content is not None else "I couldn't generate a response. Please try again."
        
        # Return response directly
        return {
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


