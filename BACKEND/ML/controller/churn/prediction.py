from fastapi import APIRouter, File, UploadFile, Form, Depends
from pydantic import BaseModel
from src.Churn.pipeline.prediction import ChurnController
from typing_extensions import Optional, Dict, Any
from utils.auth import require_staff_or_admin

router = APIRouter()

class ChurnResponse(BaseModel):
    payload: Dict[str, Any]
    mlflow_url: Optional[str] = None

@router.post("/", response_model=ChurnResponse)
async def predict_churn(
    file: UploadFile = File(...),
    model_version: str = Form(default="1"),
    scaler_version: str = Form(default="scaler/scaler_churn_version_20250705T125012.pkl"),
    run_id: str = Form(default="e26506b0b99247c6bcec84a630fa665e"),
    # current_user: Dict[str, Any] = Depends(require_staff_or_admin)
    ):
    """
    Predict customer churn using uploaded data.

    **Access Control**: Requires 'staff' or 'admin' role.

    - **file**: CSV file containing customer data for churn prediction
    - **model_version**: Version of the churn model to use
    - **scaler_version**: Version of the data scaler to use
    - **run_id**: MLflow run ID for model artifacts
    - **reference_data**: S3 path to reference data for drift detection
    """
    result = await ChurnController.predict_churn(
        file=file,
        model_version=model_version,
        scaler_version=scaler_version,
        run_id=run_id
    )
    

    if isinstance(result, tuple):
        error_message, _ = result
        return ChurnResponse(
            payload={"error": error_message},
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
        )
    elif isinstance(result, dict):
        return ChurnResponse(
            payload=result,
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
        )
    else:
        return ChurnResponse(
            payload={"message": str(result)},
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
        )