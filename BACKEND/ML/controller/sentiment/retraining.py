from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import  Optional
from src.Sentiment.pipeline.main_pipeline import WorkflowRunner
from src.Sentiment.utils.logging import logger

router = APIRouter()

class WorkflowResponse(BaseModel):
    status: str
    message: str



@router.post("/", response_model=WorkflowResponse)
async def train_model(
    file: Optional[UploadFile] = File(None)
):
    """
    Run the complete model training workflow.
    
    - **file**: Optional CSV/Excel file for training data. If not provided, will use existing data file.
    """
    try:
        workflow_runner = WorkflowRunner()
        await workflow_runner.run(uploaded_file=file)
        
        return WorkflowResponse(
            status="success",
            message="Model training workflow completed successfully",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow failed with unexpected error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Workflow failed with unexpected error: {str(e)}"
        )

@router.get("/status")
async def get_workflow_status():
    """
    Check the status of the workflow system.
    """
    try:
        workflow_runner = WorkflowRunner()
        data_file_exists = workflow_runner.check_data_file_exists()
        
        return {
            "status": "ready",
            "data_file_exists": data_file_exists,
            "message": "Workflow system is ready" if data_file_exists else "No data file found - upload required"
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )