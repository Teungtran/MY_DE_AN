from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks
from pydantic import BaseModel
from src.Churn.pipeline.prediction import ChurnController
from typing_extensions import Optional
router = APIRouter()


class ChurnResponse(BaseModel):
    message: str

@router.post("/", response_model=ChurnResponse)
async def predict_churn(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_version: str = Form(default="1"),
    scaler_version: str = Form(default="scaler_churn_version_20250703T004330.pkl"),
    run_id: str = Form(default="8743cf1d61744dedb1dab8a4342e67f6"),
    reference_data: Optional[str] = Form(default=None)
    ) :
    return await ChurnController.predict_churn(background_tasks=background_tasks, file=file, model_version=model_version, scaler_version=scaler_version, run_id=run_id,reference_data=reference_data)
