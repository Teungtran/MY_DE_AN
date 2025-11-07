from fastapi import UploadFile, HTTPException,Form,BackgroundTasks
from src.Sentiment.components.support import import_data
from typing_extensions import Optional
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from src.Sentiment.components.data_ingestion import DataIngestion
from src.Sentiment.config.configuration import ConfigurationManager
import joblib 
import mlflow
from src.Sentiment.utils.logging import logger
from src.Sentiment.utils.visualize_ouput import rating_distribution
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from datetime import datetime
import time
import os
import dagshub
import tempfile
import os
import boto3
def calculate_rating(ratings):
    return [min(5.0, max(0.5, round(r[0] * 10) / 2)) for r in ratings]
class PredictionPipeline:
    def __init__(self, model_uri: str, tokenizer_uri: str):
        try:
            config = ConfigurationManager().get_mlflow_config()
            # Get DagsHub token from environment
            dagshub_token = os.getenv("MLFLOW_TRACKING_PASSWORD")
            if dagshub_token:
                # Include credentials in tracking URI
                tracking_uri = config.tracking_uri.replace(
                    "https://",
                    f"https://{config.dagshub_username}:{dagshub_token}@"
                )
            else:
                tracking_uri = config.tracking_uri
            mlflow.set_tracking_uri(tracking_uri)
            logger.info(f"MLflow tracking URI set to: {mlflow.get_tracking_uri()}")
            self.model = mlflow.pyfunc.load_model(model_uri)
            tokenizer_path = mlflow.artifacts.download_artifacts(artifact_uri=tokenizer_uri)
            self.tokenizer = joblib.load(tokenizer_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model or tokenizer: {e}")
    
    def preprocess_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess text data for sentiment analysis - prefer 'review', else fallback to longest text column."""
        df.columns = df.columns.str.lower()

        review_col = None

        if 'review' in df.columns:
            review_col = 'review'
            logger.info("Using 'review' column for sentiment analysis.")
        else:
            text_columns = [col for col in df.columns if df[col].dtype == 'object']
            if text_columns:
                review_col = max(text_columns, key=lambda col: df[col].astype(str).str.len().mean())
                logger.warning(f"'review' column not found. Falling back to longest text column: '{review_col}'")
        
        if review_col is None:
            raise KeyError("No suitable text column found for sentiment analysis.")

        # Step 3: Process chosen column
        df_processed = df.copy()
        df_processed['review'] = df_processed[review_col].astype(str).str.strip()

        # Step 4: Apply preprocessing
        data_ingestion = DataIngestion(config=ConfigurationManager().get_data_ingestion_config())
        df_processed['review'] = [
            data_ingestion._preprocess_text_fast(text) for text in df_processed['review']
        ]

        return df_processed

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
            
            # Get DagsHub token from environment and set it for dagshub.get_token()
            dagshub_token = os.getenv("MLFLOW_TRACKING_PASSWORD")
            if dagshub_token:
                # Set token in environment for dagshub.get_token() to find
                os.environ["DAGSHUB_USER_TOKEN"] = dagshub_token
            
            dagshub.init(
                repo_owner=mlflow_config.dagshub_username,
                repo_name=mlflow_config.dagshub_repo_name,
                mlflow=True
            )
            
            # Include credentials in tracking URI for MLflow authentication
            if dagshub_token:
                tracking_uri = mlflow_config.tracking_uri.replace(
                    "https://",
                    f"https://{mlflow_config.dagshub_username}:{dagshub_token}@"
                )
            else:
                tracking_uri = mlflow_config.tracking_uri
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(mlflow_config.prediction_experiment_name)  
            
            with mlflow.start_run(run_name=f"sentiment_prediction_run_{time_str}"):
                data_ingestion = DataIngestion(config=data_ingestion_config)
                df = data_ingestion.load_data_for_prediction()
                df_processed = self.preprocess_text(df)
                
                sequences = self.tokenizer.texts_to_sequences(df_processed['review'].tolist())
                padded_sequences = pad_sequences(sequences, maxlen=200)
                ratings = self.model.predict(padded_sequences)
                
                df_processed['predicted_sentiment'] = calculate_rating(ratings)
                # Create 'rating' column for visualization function
                df_processed['rating'] = df_processed['predicted_sentiment']
                # Calculate rating distribution for metrics
                rating_counts = df_processed['rating'].value_counts()
                avg_rating = float(df_processed['rating'].mean())
                
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
                
                # Calculate prediction confidence for TensorFlow model
                try:
                    # For rating prediction, confidence can be measured by the spread/variance
                    rating_variance = float(df_processed['rating'].var())
                    # Lower variance indicates more consistent (confident) predictions
                    average_confidence = float(max(0.5, min(1.0, 1.0 - (rating_variance / 5.0))))
                except Exception as e:
                    logger.warning(f"Could not calculate confidence: {e}")
                    average_confidence = None 
                
                end_time = time.time()
                end_datetime = datetime.now()
                processing_time = end_time - start_time

                logger.info(f"Prediction processing time: {processing_time:.2f} seconds")
                logger.info(f"Started at: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Completed at: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Create visualization
                plot_path = rating_distribution(df_processed)
                if plot_path != "visualization_failed.png" and os.path.exists(plot_path):
                    mlflow.log_artifact(plot_path, "visualization")
                    os.remove(plot_path)
                else:
                    logger.warning("Visualization creation failed, skipping artifact logging")
                
                # Log metrics
                mlflow.log_metric("processing_time_seconds", processing_time)
                mlflow.log_metric("average_rating", avg_rating)
                mlflow.log_metric("rating_variance", float(rating_variance) if 'rating_variance' in locals() else 0.0)
                
                # Log rating distribution
                for rating, count in rating_counts.items():
                    mlflow.log_metric(f"count_rating_{rating}", count)
                
                mlflow.log_param("start_time", start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                mlflow.log_param("end_time", end_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                mlflow.log_param("rawdata_records", len(df))
                mlflow.log_metric("records_processed", len(df_processed))
                
                message = f"📊 Rating Analysis Complete:\n"
                message += f"• Average Rating: {avg_rating:.2f}/5.0\n"
                message += f"• Total Records Processed: {len(df_processed)}\n"
                message += f"• Rating Distribution: {dict(rating_counts.sort_index())}\n"
                
                CONFIDENCE_THRESHOLD = threshold_config.confidence_threshold
                if average_confidence is not None:
                    mlflow.log_metric("average_prediction_confidence", average_confidence)
                    message += f"• Prediction Confidence: {average_confidence:.2%}\n"

                    if average_confidence < CONFIDENCE_THRESHOLD:
                        message += (
                            f"⚠️ Prediction confidence ({average_confidence:.2%}) is below threshold "
                            f"({CONFIDENCE_THRESHOLD:.2%}). Consider retraining the model."
                        )
                    else:
                        message += (
                            f"✅ Prediction confidence ({average_confidence:.2%}) meets quality threshold "
                            f"({CONFIDENCE_THRESHOLD:.2%})."
                        )
                mlflow.log_text(message, "prediction_summary.txt")
            
            # Read actual results from S3 if upload was successful
            s3_results_data = None
            if s3_url:
                try:
                    # Download the file from S3 and parse it
                    import requests
                    response = requests.get(s3_url)
                    if response.status_code == 200:
                        from io import StringIO
                        s3_df = pd.read_csv(StringIO(response.text))
                        s3_df = s3_df.where(pd.notnull(s3_df), None)
                        # Convert numpy types to native Python types for JSON serialization
                        import numpy as np
                        s3_results_data = []
                        for record in s3_df.to_dict(orient="records"):
                            converted_record = {}
                            for k, v in record.items():
                                if v is None or pd.isna(v):
                                    converted_record[k] = None
                                elif isinstance(v, (np.integer, np.int64, np.int32)):
                                    converted_record[k] = int(v)
                                elif isinstance(v, (np.floating, np.float64, np.float32)):
                                    converted_record[k] = float(v)
                                else:
                                    converted_record[k] = v
                            s3_results_data.append(converted_record)
                        logger.info(f"Successfully retrieved {len(s3_results_data)} records from S3")
                    else:
                        logger.warning(f"Failed to retrieve S3 file: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"Error retrieving S3 results: {e}")
            
            # Convert numpy types to native Python types for JSON serialization
            rating_dist = rating_counts.sort_index()
            rating_dist_dict = {float(k): int(v) for k, v in rating_dist.items()}
            
            return {
                "message": message,
                "s3_url": s3_url,
                "s3_results_data": s3_results_data,
                "summary": {
                    "total_records": int(len(df_processed)),
                    "average_rating": float(avg_rating),
                    "rating_distribution": rating_dist_dict
                }
            }

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
        result = await pipeline.predict()

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleanup: Deleted input file {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete input file during cleanup: {e}")
        
        # Add timestamp to result
        result["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return result

    except Exception as e:
        logger.error(f"Background prediction task error: {e}")
        return {
            "error": f"Prediction error: {e}",
            "s3_url": None,
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