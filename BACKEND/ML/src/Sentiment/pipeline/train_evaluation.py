from src.Sentiment.config.configuration import ConfigurationManager
from src.Sentiment.components.model_training import TrainAndEvaluateModel
from src.Sentiment.utils.logging import logger


STAGE_NAME = "TRAIN_AND_EVALUATE_MODEL"


class TrainEvaluationPipeline:
    def __init__(self, mlflow_config):
        self.mlflow_config = mlflow_config
    def main(self, base_model, train_data, test_data,tokenizer):
        
        logger.info(f">>> Stage {STAGE_NAME} started <<<")
        training_config = ConfigurationManager().get_training_config()
        evaluation_config = ConfigurationManager().get_evaluation_config()
        
        # No need to start a new MLflow run here as we'll use the one from main_pipeline
        model_processor = TrainAndEvaluateModel(
            config_train=training_config,
            config_eval=evaluation_config
        )
        
        model, metrics = model_processor.train_and_evaluate(
            base_model=base_model,
            test_data=test_data,
            train_data=train_data,
            tokenizer=tokenizer
        )
        logger.info(f">>> Stage {STAGE_NAME} completed <<<")
        return model, metrics

