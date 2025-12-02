from fastapi import UploadFile, HTTPException,Form,BackgroundTasks
from src.Churn.components.support import import_data,most_common,get_dummies
from typing_extensions import Optional
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from src.Churn.components.data_ingestion import DataIngestion
from src.Churn.config.configuration import ConfigurationManager, WebhookConfig
import joblib 
import mlflow
from src.Churn.utils.logging import logger
from src.Churn.utils.visualize_ouput import visualize_customer_churn

from datetime import datetime
import time
import os
import dagshub
import dagshub.auth
import tempfile
import os
import boto3
web_hook_url = WebhookConfig().url

class PredictionPipeline:
    def __init__(self, model_uri: str, scaler_uri: str,):
        pass
    
        try:
            config = ConfigurationManager().get_mlflow_config()
            # Get DagsHub token from environment
            dagshub_token = os.getenv("DAGSHUB_USER_TOKEN")
            if dagshub_token:
                dagshub.auth.add_app_token(dagshub_token) 
                tracking_uri = config.tracking_uri.replace(
                    "https://",
                    f"https://{config.dagshub_username}:{dagshub_token}@"
                )
            else:
                tracking_uri = config.tracking_uri
            mlflow.set_tracking_uri(tracking_uri)
            logger.info(f"MLflow tracking URI set to: {mlflow.get_tracking_uri()}")
            self.model = mlflow.pyfunc.load_model(model_uri)
            scaler_path = mlflow.artifacts.download_artifacts(artifact_uri=scaler_uri)
            self.scaler = joblib.load(scaler_path)
        except Exception as e:
                raise RuntimeError(f"Failed to load model or scaler: {e}")
    def process_data_for_churn(self,df_input: pd.DataFrame):
        df_input.columns = df_input.columns.map(str.strip)
        cols_to_drop = {"Age"}
        df_input.drop(columns=[col for col in cols_to_drop if col in df_input.columns], inplace=True)    
        df_input.dropna(inplace=True)
        if 'Price' not in df_input.columns:
            df_input['Price'] = df_input['Product Price']
        else:
            print("Price column already exists, skipping.") 
        df_input['TotalSpent'] = df_input['Quantity'] * df_input['Price']
        df_features = df_input.groupby("customer_id", as_index=False, sort=False).agg(
            LastPurchaseDate = ("Purchase Date","max"),
            Favoured_Product_Categories = ("Product Category", lambda x: most_common(list(x))),
            Frequency = ("Purchase Date", "count"),
            TotalSpent = ("TotalSpent", "sum"),
            Favoured_Payment_Methods = ("Payment Method", lambda x: most_common(list(x))),
            Customer_Name = ("Customer Name", "first"),
            Customer_Label = ("Customer_Labels", "first"),
        )
        df_features = df_features.drop_duplicates(subset=['Customer_Name'], keep='first')
        df_features['LastPurchaseDate'] = pd.to_datetime(df_features['LastPurchaseDate'])
        df_features['LastPurchaseDate'] = df_features['LastPurchaseDate'].dt.date
        df_features['LastPurchaseDate'] = pd.to_datetime(df_features['LastPurchaseDate'])
        max_LastBuyingDate = df_features["LastPurchaseDate"].max()
        df_features['Recency'] = (max_LastBuyingDate - df_features['LastPurchaseDate']).dt.days
        df_features['LastPurchaseDate'] = df_features['LastPurchaseDate'].dt.date
        df_features['Avg_Spend_Per_Purchase'] = df_features['TotalSpent']/df_features['Frequency'].replace(0,1)
        df_features['Purchase_Consistency'] = df_features['Recency'] / df_features['Frequency'].replace(0, 1)
        return df_features
    def encode_churn(self, df_features):
        """
        Encode categorical features using one-hot encoding.
        Assumes customer_id and Customer_Name have already been dropped.
        """
        df_copy = df_features.copy()
        df_features_encode = get_dummies(df_copy)
        return df_features_encode
    
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
            object_key = f"churn_data_store/prediction/prediction_churn_{timestamp}.csv"
            
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
            
            dagshub_token = os.getenv("DAGSHUB_USER_TOKEN")

            
            dagshub.init(
                repo_owner=mlflow_config.dagshub_username,
                repo_name=mlflow_config.dagshub_repo_name,
                mlflow=True
            )
            
            if dagshub_token:
                dagshub.auth.add_app_token(dagshub_token) 
                tracking_uri = mlflow_config.tracking_uri.replace(
                    "https://",
                    f"https://{mlflow_config.dagshub_username}:{dagshub_token}@"
                )
            else:
                tracking_uri = mlflow_config.tracking_uri
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(mlflow_config.prediction_experiment_name)   
            with mlflow.start_run(run_name=f"prediction_run_{time_str}"):
                data_ingestion = DataIngestion(config=data_ingestion_config)
                df = data_ingestion.load_data()
                df_features = self.process_data_for_churn(df)

                
                df_features_for_prediction = df_features.copy()
                
                columns_to_drop = []
                if "customer_id" in df_features_for_prediction.columns:
                    columns_to_drop.append("customer_id")
                if "LastPurchaseDate" in df_features_for_prediction.columns:
                    columns_to_drop.append("LastPurchaseDate")
                if "Customer_Name" in df_features_for_prediction.columns:
                    columns_to_drop.append("Customer_Name")
                
                if columns_to_drop:
                    logger.info(f"Dropping columns for prediction: {columns_to_drop}")
                    df_features_for_prediction.drop(columns=columns_to_drop, inplace=True)
                
                # Encode the features for prediction
                df_encoded = self.encode_churn(df_features_for_prediction)

                X = self.scaler.transform(df_encoded)
                
                # Access the underlying sklearn model to use predict_proba
                sklearn_model = self.model._model_impl
                y_pred = sklearn_model.predict_proba(X)[:, 1]
                
                # Add predictions back to the original df_features
                df_features['Churn_RATE'] = y_pred
                
                # Count churn risk levels (Churn_RATE is a probability, not binary)
                # Use a threshold of 0.5 to categorize high risk vs low risk
                threshold = 0.5
                count_churn = int((df_features['Churn_RATE'] >= threshold).sum())
                count_not_churn = int((df_features['Churn_RATE'] < threshold).sum())
                
                s3_url = None
                prediction_csv_path = None
                
                try:
                    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                        prediction_csv_path = temp_file.name
                        df_features.to_csv(prediction_csv_path, index=False)
                        logger.info(f"Successfully saved prediction results to {prediction_csv_path}")
                    
                    s3_url = self.upload_to_s3(prediction_csv_path)
                    mlflow.set_tag("prediction_file", s3_url)
                    logger.info(f"Uploaded prediction file to S3: {s3_url}")

                    os.remove(prediction_csv_path)
                    logger.info(f"Deleted temporary prediction file: {prediction_csv_path}")

                except Exception as e:
                    logger.error(f"An error occurred during prediction saving or cleanup: {e}")

                
                try:    
                    # sklearn_model is already defined above, reuse it
                    y_proba = sklearn_model.predict_proba(X)
                    max_confidence = y_proba.max(axis=1)
                    average_confidence = float(max_confidence.mean())
                except (AttributeError, NameError) as e:
                    logger.warning(f"Could not calculate confidence: {e}")
                    average_confidence = None 
                end_time = time.time()
                end_datetime = datetime.now()
                processing_time = end_time - start_time

                logger.info(f"Prediction processing time: {processing_time:.2f} seconds")
                logger.info(f"Started at: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Completed at: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Generate visualization
                plot_path = visualize_customer_churn(df_features)
                if plot_path != "visualization_failed.png" and os.path.exists(plot_path):
                    mlflow.log_artifact(plot_path, "visualization")
                    os.remove(plot_path)
                else:
                    logger.warning("Visualization creation failed, skipping artifact logging")
                mlflow.log_metric("processing_time_seconds", processing_time)
                mlflow.log_metric("count_churn", count_churn)
                mlflow.log_metric("count_not_churn", count_not_churn)
                mlflow.log_param("start_time", start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                mlflow.log_param("end_time", end_datetime.strftime('%Y-%m-%d %H:%M:%S'))
                mlflow.log_param("rawdata_records", len(df))
                mlflow.log_metric("records_processed", len(df_encoded))
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
            return {
                "message": message,
                "s3_url": s3_url,
                "s3_results_data": s3_results_data,
                "summary": {
                    "total_records": int(len(df_features)),
                    "churn_count": int(count_churn),
                    "not_churn_count": int(count_not_churn),
                    "average_confidence": float(average_confidence) if average_confidence is not None else None
                }
            }

        except Exception as e:
            raise RuntimeError(f"Prediction error: {e}")
        
async def run_prediction_task(
    file_path: str,
    model_version: str,
    scaler_version: str,
    run_id: str,
):
    """
    Background task to run prediction pipeline and notify webhook.
    """
    try:
        model_uri = f"models:/RandomForestClassifier/{model_version}"
        scaler_uri = f"runs:/{run_id}/{scaler_version}"
        pipeline = PredictionPipeline(model_uri, scaler_uri)
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


class ChurnController:
    @staticmethod
    async def predict_churn(
        file: UploadFile,
        model_version: str = Form(default="1"),
        scaler_version: str = Form(default="scaler_churn_version_20250701T105905.pkl"),
        run_id: str = Form(default="b523ba441ea0465085716dcebb916294")
        ):
        """
        Predict churn using uploaded file and dynamic model/scaler versions.
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
                scaler_version=scaler_version,
                run_id=run_id,
            )

            return payload

        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")