from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from io import BytesIO
import pandas as pd
from src.Churn.pipeline.main_pipeline import WorkflowRunner
from src.Churn.utils.logging import logger
from utils.auth import require_admin_role

router = APIRouter()

class WorkflowResponse(BaseModel):
    status: str
    message: str
    mlflow_url: Optional[str] = None



@router.post("/", response_model=WorkflowResponse)
async def train_model(
    file: Optional[UploadFile] = File(None),
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Run the complete churn model training workflow.

    **Access Control**: Requires 'admin' role only.

    - **file**: Optional CSV/Excel file for training data. If not provided, will use existing data file.

    This endpoint initiates the complete ML pipeline including:
    - Data ingestion and preprocessing
    - Feature engineering
    - Model training and evaluation
    - Model versioning and artifact storage
    - Performance metrics calculation
    """
    try:
        # Log the admin user who initiated training
        logger.info(f"Churn model training initiated by admin user: {current_user['user_id']} ({current_user['email']})")


        workflow_runner = WorkflowRunner()
        await workflow_runner.run(uploaded_file=file)
        return WorkflowResponse(
            status="success",
            message="Model training workflow completed successfully",
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow",
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
async def get_workflow_status(
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Check the status of the workflow system.

    **Access Control**: Requires 'admin' role only.
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