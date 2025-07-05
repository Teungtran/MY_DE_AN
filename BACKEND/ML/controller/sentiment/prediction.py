from fastapi import APIRouter, File, UploadFile, Form
from pydantic import BaseModel
from src.Sentiment.pipeline.prediction import SentimentController
from typing_extensions import Optional, Dict, Any
router = APIRouter()

class SentimentResponse(BaseModel):
    payload: Dict[str, Any]

@router.post("/", response_model=SentimentResponse)
async def predict_sentiment(
    file: UploadFile = File(...),
    model_version: str = Form(default="1"),
    tokenizer_version: str = Form(default="tokenizer/tokenizer_version_20250701T105905.pkl"),
    run_id: str = Form(default="a523ba441ea0465085716dcebb916294")
    ) :
    result = await SentimentController.predict_sentiment(
        file=file, 
        model_version=model_version, 
        tokenizer_version=tokenizer_version, 
        run_id=run_id
    )
    
    # Handle different response types
    if isinstance(result, tuple):
        error_message, _ = result
        return {"payload": {"error": error_message}}
    elif isinstance(result, dict):
        return {"payload": result}
    else:
        return {"payload": {"message": str(result)}}