from src.Sentiment.config.configuration import ConfigurationManager
from src.Sentiment.components.base_model import PrepareBaseModel
from src.Sentiment.utils.logging import logger
import mlflow
import dagshub
STAGE_NAME = "Prepare base model"


class ModelPreparationPipeline:
    def __init__(self, mlflow_config):
        self.mlflow_config = mlflow_config
    def main(self, train_data):
        logger.info(f">>> Stage {STAGE_NAME} started <<<")
        prepare_base_model_config = ConfigurationManager().get_prepare_base_model_config()
        
        mlflow.log_params({
            "batch_size": prepare_base_model_config.batch_size,
            "dropout_rate": prepare_base_model_config.dropout_rate,
            "embedding_dim": prepare_base_model_config.embedding_dim,
            "epochs": prepare_base_model_config.epochs,
            "filters": prepare_base_model_config.filters,
            "kernel_size": prepare_base_model_config.kernel_size,
            "maxlen": prepare_base_model_config.maxlen,
            "num_words": prepare_base_model_config.num_words
        })
        prepare_base_model = PrepareBaseModel(config=prepare_base_model_config)
        model, base_model_path, tokenizer_path , tokenizer = prepare_base_model.full_model(train_data)
        
        logger.info(f">>> Stage {STAGE_NAME} completed <<<")
        return model, base_model_path, tokenizer_path , tokenizer

