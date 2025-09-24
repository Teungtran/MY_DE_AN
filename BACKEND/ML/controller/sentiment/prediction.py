from fastapi import APIRouter, File, UploadFile, Form, Depends
from pydantic import BaseModel
from src.Sentiment.pipeline.prediction import SentimentController
from typing_extensions import Optional, Dict, Any
from utils.auth import require_staff_or_admin

router = APIRouter()

class SentimentResponse(BaseModel):
    payload: Dict[str, Any]
    user_info: Optional[Dict[str, str]] = None
    mlflow_url: Optional[str] = None

@router.post("/", response_model=SentimentResponse)
async def predict_sentiment(
    file: UploadFile = File(...),
    model_version: str = Form(default="1"),
    tokenizer_version: str = Form(default="tokenizer/tokenizer_version_20250810T020107.pkl"),
    run_id: str = Form(default="e5eb544e473d4a7b9109b98c5255de04"),
    current_user: Dict[str, Any] = Depends(require_staff_or_admin)
    ) :
    """
    Predict sentiment using uploaded data.

    **Access Control**: Requires 'staff' or 'admin' role.

    - **file**: CSV file containing text data for sentiment analysis
    - **model_version**: Version of the sentiment model to use
    - **tokenizer_version**: Version of the tokenizer to use
    - **run_id**: MLflow run ID for model artifacts
    """
    result = await SentimentController.predict_sentiment(
        file=file, 
        model_version=model_version, 
        tokenizer_version=tokenizer_version, 
        run_id=run_id
    )
    
    # Include user info in response
    user_info = {
        "user_id": current_user["user_id"],
        "role": current_user["role"],
        "email": current_user["email"]
    }
    
    # Handle different response types
    if isinstance(result, tuple):
        error_message, _ = result
        return SentimentResponse(
            payload={"error": error_message},
            user_info=user_info,
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
        )
    elif isinstance(result, dict):
        return SentimentResponse(
            payload=result,
            user_info=user_info,
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
        )
    else:
        return SentimentResponse(
            payload={"message": str(result)},
            user_info=user_info,
            mlflow_url="https://dagshub.com/Teungtran/MY_DE_AN.mlflow"
        )