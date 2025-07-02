from src.Sentiment.config.configuration import ConfigurationManager
from src.Sentiment.components.data_ingestion import DataIngestion
from src.Sentiment.utils.logging import logger


STAGE_NAME = "Data Ingestion stage"
class DataPreparationPipeline:
    def main(self):
        logger.info(f">>> Stage {STAGE_NAME} started <<<")
        
        config = ConfigurationManager()
        data_ingestion_config = config.get_data_ingestion_config()
        data_ingestion = DataIngestion(config=data_ingestion_config)
        
        df_processed, train_path, test_path,train_data,test_data = data_ingestion.data_ingestion_pipeline()
        
        logger.info(f">>> Stage {STAGE_NAME} completed <<<")
        return df_processed, train_path, test_path, train_data, test_data

