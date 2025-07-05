from fastapi import UploadFile, HTTPException,Form,BackgroundTasks
from src.Sentiment.components.support import import_data,most_common,get_dummies
from typing_extensions import Optional
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from src.Sentiment.components.data_ingestion import DataIngestion
from src.Sentiment.config.configuration import ConfigurationManager, WebhookConfig
import joblib 
import mlflow
from src.Sentiment.utils.logging import logger
from src.Sentiment.utils.visualize_ouput import rating_distribution

from datetime import datetime
import time
import os
import dagshub
import tempfile
import os
import boto3

class PredictionPipeline:
    def __init__(self, model_uri: str, tokenizer_uri: str):
        try:
            config = ConfigurationManager().get_mlflow_config()
            mlflow.set_tracking_uri(config.tracking_uri)
            logger.info(f"MLflow tracking URI set to: {mlflow.get_tracking_uri()}")
            self.model = mlflow.pyfunc.load_model(model_uri)
            tokenizer_path = mlflow.artifacts.download_artifacts(artifact_uri=tokenizer_uri)
            self.tokenizer = joblib.load(tokenizer_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model or tokenizer: {e}")
    
    def preprocess_text(self, df):
        """Preprocess text data for sentiment analysis"""
        data_ingestion = DataIngestion(config=ConfigurationManager().get_data_ingestion_config())
        return data_ingestion.preprocess_data(df)
    
    def upload_to_s3(self, file_path):
        """
        Upload a file to S3 and return the public URL
        """
        try:
            config = ConfigurationManager().get_cloud_storage_push_config()
            bucket_name = config.bucket_name
            region_name = config.region_name
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.aws_key_id,
                aws_secret_access_key=config.aws_secret_key,
                region_name=region_name
            )
            
            timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
            object_key = f"sentiment_data_store/prediction/prediction__sentiment_{timestamp}.csv"
            
            s3_client.upload_file(file_path, bucket_name, object_key)
            
            url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{object_key}"
            logger.info(f"Successfully uploaded prediction results to S3: {url}")
            
            return url
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    async def predict(self):
        try:
            start_time = time.time()
            start_datetime = datetime.now()
            time_str = start_datetime.strftime('%Y%m%dT%H%M%S')
            config_manager = ConfigurationManager()
            data_ingestion_config = config_manager.get_data_ingestion_config()
            mlflow_config = config_manager.get_mlflow_config()
            threshold_config = config_manager.get_threshold_config()
            
            dagshub.init(
                repo_owner=mlflow_config.dagshub_username,
                repo_name=mlflow_config.dagshub_repo_name,
                mlflow=True
            )
            mlflow.set_tracking_uri(mlflow_config.tracking_uri)
            mlflow.set_experiment(mlflow_config.prediction_experiment_name)  
            
            with mlflow.start_run(run_name=f"sentiment_prediction_run_{time_str}"):
                data_ingestion = DataIngestion(config=data_ingestion_config)
                df = data_ingestion.load_data()
                df_processed = self.preprocess_text(df)
                
                X = self.tokenizer.transform(df_processed['review'])
                y_pred = self.model.predict(X)
                
                df_processed['predicted_sentiment'] = y_pred
                
                counts = df_processed['predicted_sentiment'].value_counts()
                count_positive = counts.get(1, 0)
                count_negative = counts.get(0, 0)
                
                s3_url = None
                prediction_csv_path = None
                
                try:
                    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                        prediction_csv_path = temp_file.name
                        df_processed.to_csv(prediction_csv_path, index=False)
                        logger.info(f"Successfully saved prediction results to {prediction_csv_path}")
                    
                    s3_url = self.upload_to_s3(prediction_csv_path)
                    mlflow.set_tag("prediction_file", s3_url)
                    logger.info(f"Uploaded prediction file to S3: {s3_url}")

                    os.remove(prediction_csv_path)
                    logger.info(f"Deleted temporary prediction file: {prediction_csv_path}")

                except Exception as e:
                    logger.error(f"An error occurred during prediction saving or cleanup: {e}")
                
                try:    
                    sklearn_model = self.model._model_impl  
                    y_proba = sklearn_model.predict_proba(X)
                    max_confidence = y_proba.max(axis=1)
                    average_confidence = max_confidence.mean()
                except AttributeError:
                    average_confidence = None 
                
                end_time = time.time()
                end_datetime = datetime.now()
                processing_time = end_time - start_time

                logger.info(f"Prediction processing time: {processing_time:.2f} seconds")
                logger.info(f"Started at: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Completed at: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Create visualization
                plot_path = rating_distribution(df_processed)
                mlflow.log_artifact(plot_path, "visualization")
                os.remove(plot_path)
                
                # Log metrics
                mlflow.log_metric("processing_time_seconds", processing_time)
                mlflow.log_metric("count_positive", count_positive)
                mlflow.log_metric("count_negative", count_negative)
                mlflow.log_param("start_time", start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                mlflow.log_param("end_time", end_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                mlflow.log_param("rawdata_records", len(df))
                mlflow.log_metric("records_processed", len(df_processed))
                
                message = ""
                CONFIDENCE_THRESHOLD = threshold_config.confidence_threshold
                if average_confidence is not None:
                    mlflow.log_metric("average_prediction_confidence", average_confidence)

                    if average_confidence < CONFIDENCE_THRESHOLD:
                        message += (
                            f"⚠️ Average prediction confidence ({average_confidence:.2%}) is below the threshold "
                            f"of {CONFIDENCE_THRESHOLD:.2%}. Consider retraining the model."
                        )
                    else:
                        message += (
                            f"✅ Average prediction confidence ({average_confidence:.2%}) is above the threshold "
                            f"of {CONFIDENCE_THRESHOLD:.2%}. No further action required."
                        )
                mlflow.log_text(message, "prediction_summary.txt")
            return message, s3_url

        except Exception as e:
            raise RuntimeError(f"Prediction error: {e}")
        
async def run_prediction_task(
    file_path: str,
    model_version: str,
    tokenizer_version: str,
    run_id: str,
):
    """
    Background task to run prediction pipeline and notify webhook.
    """
    try:
        model_uri = f"models:/CNN/{model_version}"
        tokenizer_uri = f"runs:/{run_id}/{tokenizer_version}"
        pipeline = PredictionPipeline(model_uri, tokenizer_uri)
        message, s3_url = await pipeline.predict()

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleanup: Deleted input file {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete input file during cleanup: {e}")
        
        payload = {
            "message": message,
            "prediction_url": s3_url,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return payload

    except Exception as e:
        logger.error(f"Background prediction task error: {e}")
        return {
            "error": f"Prediction error: {e}",
            "prediction_url": None,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class SentimentController:
    @staticmethod
    async def predict_sentiment(
        file: UploadFile,
        model_version: str = Form(default="1"),
        tokenizer_version: str = Form(default="tokenizer/tokenizer_version_20250701T105905.pkl"),
        run_id: str = Form(default="a523ba441ea0465085716dcebb916294"),
    ):
        """
        Predict sentiment using uploaded file and dynamic model/tokenizer versions.
        """
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        config_manager = ConfigurationManager()
        data_ingestion_config = config_manager.get_data_ingestion_config()
        input_file_path = data_ingestion_config.local_data_file

        try:
            await import_data(file)
                
            payload = await run_prediction_task(
                file_path=input_file_path,
                model_version=model_version,
                tokenizer_version=tokenizer_version,
                run_id=run_id
            )

            return payload

        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")