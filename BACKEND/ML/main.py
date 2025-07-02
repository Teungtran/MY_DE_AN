from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import mlflow
from dotenv import load_dotenv
from controller.churn import prediction, retraining

# Load environment variables
load_dotenv()

mlflow.set_tracking_uri("https://dagshub.com/Teungtran/MY_DE_AN.mlflow")

# Create FastAPI app
app = FastAPI(
    title="Churn Prediction API",
    description="API for customer churn prediction and model retraining",
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
app.include_router(prediction.router, prefix="/churn_prediction", tags=["MLOps controller"])
app.include_router(retraining.router, prefix="/churn_training", tags=["MLOps controller"])

@app.get("/")
async def root():
    return {"message": "Welcome to the MLOps API. Use /docs to view the API documentation."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)
