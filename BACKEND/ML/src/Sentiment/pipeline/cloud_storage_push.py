from src.Churn.config.configuration import ConfigurationManager
from src.Churn.components.cloud_storage_push import CloudStoragePush
from src.Churn.utils.logging import logger

STAGE_NAME = "Cloud Storage Push"



class CloudStoragePushPipeline:
    def __init__(self, model_name="churn"):
        self.model_name = model_name
        
    def main(self):
        logger.info(f">>> Stage {STAGE_NAME} for {self.model_name} model started <<<")
        
        config = ConfigurationManager()
        cloud_storage_push_config = config.get_cloud_storage_push_config()
        cloud_storage_push = CloudStoragePush(config=cloud_storage_push_config, model_name=self.model_name)
        cloud_storage_push.push_to_cloud_storage()
        
        logger.info(f">>> Stage {STAGE_NAME} for {self.model_name} model completed <<<")

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run cloud storage push for specific model')
    parser.add_argument('--model', type=str, default='churn',
                        choices=['churn', 'sentiment', 'segmentation', 'timeseries'],
                        help='Model to run cloud storage push for (default: churn)')
    args = parser.parse_args()
    
    # Run the pipeline with the specified model
    pipeline = CloudStoragePushPipeline(model_name=args.model)
    pipeline.main()
