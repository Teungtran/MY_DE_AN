from fastapi import APIRouter, File, UploadFile, Form
from pydantic import BaseModel
from src.Churn.pipeline.prediction import ChurnController
from typing_extensions import Optional, Dict, Any
router = APIRouter()

class ChurnResponse(BaseModel):
    payload: Dict[str, Any]

@router.post("/", response_model=ChurnResponse)
async def predict_churn(
    file: UploadFile = File(...),
    model_version: str = Form(default="1"),
    scaler_version: str = Form(default="scaler/scaler_churn_version_20250705T125012.pkl"),
    run_id: str = Form(default="e26506b0b99247c6bcec84a630fa665e"),
    reference_data: Optional[str] = Form(default="s3://ml-dataversion/churn_data_store/churn/data_version/features_data_version_20250705T125002.csv")
    ) :
    result = await ChurnController.predict_churn(
        file=file, 
        model_version=model_version, 
        scaler_version=scaler_version, 
        run_id=run_id,
        reference_data=reference_data
    )
    
    # Handle different response types
    if isinstance(result, tuple):
        error_message, _ = result
        return {"payload": {"error": error_message}}
    elif isinstance(result, dict):
        return {"payload": result}
    else:
        return {"payload": {"message": str(result)}}