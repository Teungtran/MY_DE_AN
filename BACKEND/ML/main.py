from typing import  cast
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

# Import all controllers
from controller.sentiment import prediction as sentiment_prediction
from controller.sentiment import retraining as sentiment_retraining
from controller.churn import prediction as churn_prediction
from controller.churn import retraining as churn_retraining



# Create FastAPI app
app = FastAPI(
    title="ML Service API",
    description="Comprehensive Machine Learning API for sentiment analysis, churn prediction, and model training workflows.",
    version="1.0.0",
    docs_url=None,  # Disable /docs endpoint (we'll create a custom one)
    redoc_url=None,  # Disable /redoc endpoint (we'll create a custom one)
    openapi_url=r"/api/openapi.json",
)



# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom API docs
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI docs endpoint"""
    return get_swagger_ui_html(
        openapi_url=cast(str, app.openapi_url),
        title=f"{app.title} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )






# Include all routers with proper prefixes and tags

# Sentiment Analysis Routes
app.include_router(
    sentiment_prediction.router, 
    prefix="/v1/sentiment/predict", 
    tags=["Sentiment Analysis - Prediction"]
)
app.include_router(
    sentiment_retraining.router, 
    prefix="/v1/sentiment/train", 
    tags=["Sentiment Analysis - Training"]
)

# Churn Prediction Routes
app.include_router(
    churn_prediction.router, 
    prefix="/v1/churn/predict", 
    tags=["Churn Prediction - Prediction"]
)
app.include_router(
    churn_retraining.router, 
    prefix="/v1/churn/train", 
    tags=["Churn Prediction - Training"]
)
if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    
    # Add the parent directory to sys.path to make absolute imports work
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    

    
    # Start the server
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=False, log_level="debug")