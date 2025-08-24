import datetime
import json 
from typing import Optional, Dict
import asyncio
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from workflow.team_agents import store_team
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from .login_page import require_store_role
from report_agent.agent import DataFrameAgent
delay: float = 0.01
router = APIRouter()

class TeamChatRequest(BaseModel):
    """Schema for team chat requests"""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="User message")


@router.post("/team/chat/stream")
async def stream_team_chat(
    request: TeamChatRequest, 
    current_user: dict = Depends(require_store_role)
):
    """
    Stream chat responses from the store team (requires admin/staff role)
    """
    try:
        user_id = current_user["user_id"]
        print(f"Starting team chat stream for user {user_id}, session {request.session_id}")
        
        async def event_stream():
            try:
                # Run the store team with streaming enabled
                result = store_team.run(
                    session_id=request.session_id,
                    user_id=user_id,
                    message=request.message,
                    stream=True
                )
                
                # Handle streaming response
                if hasattr(result, '__iter__'):
                    for chunk in result:
                        if chunk:
                            # Extract content from the chunk object
                            content = ""
                            if hasattr(chunk, 'content'):
                                content = chunk.content
                            elif hasattr(chunk, 'data') and hasattr(chunk.data, 'content'):
                                content = chunk.data.content
                            else:
                                content = str(chunk)
                            
                            yield {
                                "event": "chunk",
                                "data": json.dumps({
                                    "content": content,
                                    "timestamp": datetime.datetime.now().isoformat()
                                })
                            }
                else:
                    # Extract content from single result
                    content = ""
                    if hasattr(result, 'content'):
                        content = result.content
                    elif hasattr(result, 'data') and hasattr(result.data, 'content'):
                        content = result.data.content
                    else:
                        content = str(result)
                    
                    yield {
                        "event": "chunk", 
                        "data": json.dumps({
                            "content": content,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    }
                
                # Send completion event
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "status": "completed",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                }
                
            except Exception as e:
                print(f"Error in team chat stream: {str(e)}")
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                }
        
        return EventSourceResponse(event_stream())
        
    except Exception as e:
        print(f"Failed to start team chat stream: {str(e)}")        
        raise HTTPException(status_code=500, detail=f"Failed to start chat stream: {str(e)}")

@router.post("/team/chat")
async def team_chat(
    request: TeamChatRequest, 
    current_user: dict = Depends(require_store_role)
):
    """
    Non-streaming team chat endpoint (requires admin/staff role)
    """
    try:
        user_id = current_user["user_id"]
        print(f"Starting team chat for user {user_id}, session {request.session_id}")
        
        result = store_team.run(
            session_id=request.session_id,
            user_id=user_id,
            message=request.message,
            stream=False
        )
        
        return {
            "content": str(result.content),
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "session_id": request.session_id
        }
        
    except Exception as e:
        print(f"Failed to process team chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


# Report Analysis Endpoints
@router.post("/report/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_store_role)

):
    allowed_extensions = {'.csv', '.xlsx', '.xls'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    artifact_dir = Path("report_agent/artifact")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    supported_extensions = ['.csv', '.txt', '.xlsx', '.xls']
    existing_files = [f for f in artifact_dir.iterdir() if f.suffix.lower() in supported_extensions]
    
    for existing_file in existing_files:
        try:
            existing_file.unlink()  
            print(f"Deleted old file: {existing_file.name}")
        except Exception as e:
            print(f"Could not delete {existing_file.name}: {e}")
    
    # Save the new file
    file_path = artifact_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f"File uploaded: {file.filename}")
    return {"filename": file.filename, "message": "File uploaded successfully"}

@router.post("/report/analyze")
async def report_agent(
    question: str,
    current_user: dict = Depends(require_store_role)

):
    """
    Analyze uploaded data file with a natural language question
    """
    try:
        async def event_stream():
            try:
                content = DataFrameAgent(question)
                
                # Stream the content character by character for better UX
                for i in range(0, len(content), 5):
                    chunk = content[i:i+5]
                    yield {
                        "event": "chunk",
                        "data": json.dumps({
                            "content": chunk,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    }
                    await asyncio.sleep(delay * 5)
                
                # Send completion event
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "status": "completed",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                }
                
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                }
        
        return EventSourceResponse(event_stream())
        
    except Exception as e:
        print(f"Failed to analyze file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


