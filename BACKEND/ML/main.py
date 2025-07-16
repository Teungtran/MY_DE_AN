from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from controller.churn import prediction as churn_prediction, retraining as churn_training
from controller.sentiment import prediction as sentiment_prediction, retraining as sentiment_training

# Load environment variables
load_dotenv()

# Validate required environment variables for authentication
required_env_vars = ["JWT_SECRET_KEY", "JWT_ALGORITHM"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing_vars)}")
    print("   Authentication will not work properly without these variables.")


# Create FastAPI app
app = FastAPI(
    title="MLOps API",
    description="API for MLOps operations with Role-Based Access Control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(churn_prediction.router, prefix="/churn_prediction", tags=["MLOps controller"])
app.include_router(churn_training.router, prefix="/churn_training", tags=["MLOps controller"])
app.include_router(sentiment_prediction.router, prefix="/sentiment_prediction", tags=["MLOps controller"])
app.include_router(sentiment_training.router, prefix="/sentiment_training", tags=["MLOps controller"])
@app.get("/")
async def root():
    return {
        "message": "Welcome to the MLOps API with Role-Based Access Control",
        "documentation": "/docs",
        "access_control": {
            "prediction_apis": "Requires 'staff' or 'admin' role",
            "training_apis": "Requires 'admin' role only"
        },
        "endpoints": {
            "churn_prediction": "/churn_prediction/",
            "churn_training": "/churn_training/",
            "sentiment_prediction": "/sentiment_prediction/",
            "sentiment_training": "/sentiment_training/"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888)
