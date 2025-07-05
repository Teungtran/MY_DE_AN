#!/bin/bash

# Create the directory structure needed for the churn pipeline
mkdir -p BACKEND/ML/artifacts/churn/data_ingestion
mkdir -p BACKEND/ML/artifacts/churn/data_version
mkdir -p BACKEND/ML/artifacts/churn/model_version
mkdir -p BACKEND/ML/artifacts/churn/evaluation
mkdir -p BACKEND/ML/artifacts/churn/plots
# Create the directory structure needed for the sentiment pipeline

mkdir -p BACKEND/ML/artifacts/sentiment/data_ingestion
mkdir -p BACKEND/ML/artifacts/sentiment/data_version
mkdir -p BACKEND/ML/artifacts/sentiment/model_version
mkdir -p BACKEND/ML/artifacts/sentiment/evaluation
mkdir -p BACKEND/ML/artifacts/sentiment/plots
# Create the directory structure needed for the TimeSeries pipeline
mkdir -p BACKEND/ML/artifacts/timeseries/data_ingestion
mkdir -p BACKEND/ML/artifacts/timeseries/data_version
mkdir -p BACKEND/ML/artifacts/timeseries/model_version
mkdir -p BACKEND/ML/artifacts/timeseries/evaluation
mkdir -p BACKEND/ML/artifacts/timeseries/plots

# Create the directory structure needed for the Segmentation pipeline
mkdir -p BACKEND/ML/artifacts/segmentation/data_ingestion
mkdir -p BACKEND/ML/artifacts/segmentation/data_version
mkdir -p BACKEND/ML/artifacts/segmentation/model_version
mkdir -p BACKEND/ML/artifacts/segmentation/evaluation
mkdir -p BACKEND/ML/artifacts/segmentation/plots

echo "Directory structure created successfully"

# Set up environment variables if not using IAM roles
if [ -f ".env" ]; then
  echo "Found .env file, loading environment variables"
  set -a
  source .env
  set +a
fi

echo "EC2 setup completed successfully" 