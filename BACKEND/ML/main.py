from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from controller.churn import prediction as churn_prediction, retraining as churn_training
from controller.sentiment import prediction as sentiment_prediction, retraining as sentiment_training
# Load environment variables
load_dotenv()


# Create FastAPI app
app = FastAPI(
    title="MLOps API",
    description="API for MLOps operations",
    version="1.0.0"
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
    return {"message": "Welcome to the MLOps API. Use /docs to view the API documentation."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888)
