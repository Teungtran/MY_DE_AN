from src.Sentiment.config.configuration import ConfigurationManager
from src.Sentiment.components.cloud_storage_push import CloudStoragePush
from src.Sentiment.utils.logging import logger

STAGE_NAME = "Cloud Storage Push"



class CloudStoragePushPipeline:
    def __init__(self, model_name="sentiment"):
        self.model_name = model_name
        
    def main(self):
        logger.info(f">>> Stage {STAGE_NAME} for {self.model_name} model started <<<")
        
        config = ConfigurationManager()
        cloud_storage_push_config = config.get_cloud_storage_push_config()
        cloud_storage_push = CloudStoragePush(config=cloud_storage_push_config, model_name=self.model_name)
        cloud_storage_push.push_to_cloud_storage()
        
        logger.info(f">>> Stage {STAGE_NAME} for {self.model_name} model completed <<<")

