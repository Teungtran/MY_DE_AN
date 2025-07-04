from src.Sentiment.utils.common import read_yaml, create_directories
from src.Sentiment.utils.logging import logger
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv


from src.Sentiment.entity.config_entity import (
    DataIngestionConfig,
    PrepareBaseModelConfig,
    TrainingConfig,
    EvaluationConfig,
    CloudStoragePushConfig,
    MLFlowConfig,
    ThresholdConfig
)
from pathlib import Path
# Initialize the _env_loaded variable
_env_loaded = False

def ensure_env_loaded():
    """Ensure environment variables are loaded only once."""
    global _env_loaded
    if not _env_loaded:
        load_dotenv(override=True)
        _env_loaded = True
        
class CloudConfig(BaseModel):
    aws_access_key_id: str = Field(default_factory=lambda: (ensure_env_loaded(), os.getenv("AWS_ACCESS_KEY_ID"))[1])
    aws_secret_access_key: str = Field(default_factory=lambda: (ensure_env_loaded(), os.getenv("AWS_SECRET_ACCESS_KEY"))[1])
    region_name: str = Field(default_factory=lambda: (ensure_env_loaded(), os.getenv("AWS_REGION"))[1])


class WebhookConfig(BaseModel):
    url: str = Field(default_factory=lambda: (ensure_env_loaded(), os.getenv("WEB_HOOK"))[1])
class ConfigurationManager:
    def __init__(
        self,
        config_filepath=Path("config/config.yaml"),
        model_name="sentiment"
    ):
        self.config = read_yaml(config_filepath)
        self.model_name = model_name
        create_directories([self.config.artifacts_root])
        
    def get_mlflow_config(self) -> MLFlowConfig:
        config_key = "sentiment_mlflow_config"
            
        config = getattr(self.config, config_key)
        base_experiment_name = config.experiment_name

        mlflow_config = MLFlowConfig(
            dagshub_username=config.dagshub_username,
            dagshub_repo_name=config.dagshub_repo_name,
            tracking_uri=config.tracking_uri,
            experiment_name=base_experiment_name,
            prediction_experiment_name=config.prediction_experiment_name
        )

        logger.info(f"MLFlow configuration for {self.model_name}: {mlflow_config}")
        return mlflow_config

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config_key = "sentiment_data_ingestion"
            
        config = getattr(self.config, config_key)
        
        create_directories([config.root_dir, config.data_version_dir])

        data_ingestion_config = DataIngestionConfig(
            root_dir=Path(config.root_dir),
            local_data_file=Path(config.local_data_file),
            test_size=config.test_size,
            random_state=config.random_state,
            data_version_dir=Path(config.data_version_dir)
            )

        logger.info(f"Data Ingestion config for {self.model_name}: {config}")
        return data_ingestion_config
        
    def get_prepare_base_model_config(self) -> PrepareBaseModelConfig:
        config_key = "sentiment_prepare_base_model"
            
        config = getattr(self.config, config_key)
        
        create_directories([config.model_version_dir, config.data_version_dir])


        
        prepare_base_model_config = PrepareBaseModelConfig(
            model_version_dir=Path(config.model_version_dir),
            data_version_dir=Path(config.data_version_dir),
            maxlen=config.maxlen,
            num_words=config.num_words,
            embedding_dim=config.embedding_dim,
            batch_size=config.batch_size,
            epochs=config.epochs,
            filters=config.filters,
            kernel_size=config.kernel_size,
            dropout_rate=config.dropout_rate
        )
            
    

        logger.info(f"Prepare base model config for {self.model_name}: {config}")
        return prepare_base_model_config

    def get_training_config(self) -> TrainingConfig:
        config_key = "sentiment_training" 
        config = getattr(self.config, config_key)
        
        create_directories([config.model_version_dir, config.data_version_dir])

        training_config = TrainingConfig(
            model_version_dir=Path(config.model_version_dir),
            data_version_dir=Path(config.data_version_dir),
            maxlen=config.maxlen,
            batch_size=config.batch_size,
            epochs=config.epochs,
            validation_split=config.validation_split
        )

        logger.info(f"Training config for {self.model_name}: {config}")
        return training_config

    def get_evaluation_config(self) -> EvaluationConfig:
        config_key = f"{self.model_name}_evaluation"
        if not hasattr(self.config, config_key):
            logger.warning(f"No specific evaluation config found for model {self.model_name}, using sentiment config")
            config_key = "sentiment_evaluation"
            
        config = getattr(self.config, config_key)
        
        create_directories([config.evaluation_dir, config.model_version_dir, config.data_version_dir])

        evaluation_config = EvaluationConfig(
            model_version_dir=Path(config.model_version_dir),
            data_version_dir=Path(config.data_version_dir),
            evaluation_dir=Path(config.evaluation_dir),
        )

        logger.info(f"Evaluation config for {self.model_name}: {config}")
        return evaluation_config

    def get_cloud_storage_push_config(self) -> CloudStoragePushConfig:
        config_key = "sentiment_cloud_storage_push"
            
        config = getattr(self.config, config_key)
        
        cloud_storage_push_config = CloudStoragePushConfig(
            root_dir=Path(config.root_dir),
            bucket_name=config.bucket_name,
            data_version_dir=Path(config.data_version_dir),
            evaluation_dir=Path(config.evaluation_dir),
            aws_key_id= CloudConfig().aws_access_key_id,
            aws_secret_key= CloudConfig().aws_secret_access_key,
            region_name= CloudConfig().region_name
        )

        logger.info(f"Cloud Storage Push config for {self.model_name}: {config}")
        return cloud_storage_push_config
    
    def get_threshold_config(self) -> ThresholdConfig:
        config = self.config.prediction_threshold

        threshold_config = ThresholdConfig(
            confidence_threshold=config.confidence_threshold,
            data_drift_threshold=config.data_drift_threshold

        )

        logger.info(f"MLFlow configuration: {threshold_config}")
        return threshold_config