import datetime
import asyncio
from typing_extensions import AsyncGenerator
import json 
from decimal import Decimal
from typing import Optional, Dict
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from workflow.team_agents import store_team
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from report_agent.agent import DataFrameAgent

router = APIRouter()

class TeamChatRequest(BaseModel):
    """Schema for team chat requests"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="User message")



class ReportAnalysisResponse(BaseModel):
    """Schema for report analysis responses"""
    question: str = Field(..., description="The question that was asked")
    analysis: str = Field(..., description="AI analysis result")
    timestamp: str = Field(..., description="Analysis timestamp")
    file_info: Optional[Dict] = Field(None, description="Information about the analyzed file")

@router.post("/team/chat/stream")
async def stream_team_chat(request: TeamChatRequest):
    """
    Stream chat responses from the store team
    """
    try:
        print(f"Starting team chat stream for user {request.user_id}, session {request.session_id}")
        
        async def event_stream():
            try:
                # Run the store team with streaming enabled
                result = store_team.run(
                    session_id=request.session_id,
                    user_id=request.user_id,
                    message=request.message,
                    stream=True
                )
                
                # Handle streaming response
                if hasattr(result, '__iter__'):
                    for chunk in result:
                        if chunk:
                            yield {
                                "event": "chunk",
                                "data": json.dumps({
                                    "content": str(chunk),
                                    "timestamp": datetime.datetime.now().isoformat()
                                })
                            }
                else:
                    yield {
                        "event": "chunk", 
                        "data": json.dumps({
                            "content": str(result),
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
async def team_chat(request: TeamChatRequest):
    """
    Non-streaming team chat endpoint
    """
    try:
        print(f"Starting team chat for user {request.user_id}, session {request.session_id}")
        
        result = store_team.run(
            session_id=request.session_id,
            user_id=request.user_id,
            message=request.message,
            stream=False
        )
        
        return {
            "content": str(result),
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": request.user_id,
            "session_id": request.session_id
        }
        
    except Exception as e:
        print(f"Failed to process team chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


# Report Analysis Endpoints
@router.post("/report/upload-and-analyze", response_model=ReportAnalysisResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    question: str = Form(...)
):
    """
    Upload a data file and analyze it with a natural language question
    """
    try:
        allowed_extensions = {'.csv', '.txt', '.xlsx', '.xls'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        artifact_dir = Path("report_agent/artifact")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = artifact_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"File uploaded: {file.filename}")
        
        analysis_result = DataFrameAgent(question)
        
        file_stats = file_path.stat()
        file_info = {
            "filename": file.filename,
            "size_bytes": file_stats.st_size,
            "uploaded_at": datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        }
        
        return ReportAnalysisResponse(
            question=question,
            analysis=analysis_result,
            timestamp=datetime.datetime.now().isoformat(),
            file_info=file_info
        )
        
    except Exception as e:
        print(f"Failed to upload and analyze file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


