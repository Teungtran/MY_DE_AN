import multiprocessing
import argparse
from src.Churn.utils.logging import logger
from src.Churn.pipeline.main_pipeline import WorkflowRunner as ChurnWorkflowRunner
# Import other model runners when they're available
# from src.Sentiment.pipeline.main_pipeline import WorkflowRunner as SentimentWorkflowRunner
# from src.segmentation.pipeline.main_pipeline import WorkflowRunner as SegmentationWorkflowRunner
# from src.TimeSeries.pipeline.main_pipeline import WorkflowRunner as TimeSeriesWorkflowRunner
import asyncio

async def async_main(model_name="churn"):
    """Async main execution function."""
    STAGE_NAME = f"Full {model_name.capitalize()} Model Workflow Run"

    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        
        # Select the appropriate workflow runner based on model name
        if model_name == "churn":
            runner = ChurnWorkflowRunner()
        elif model_name == "sentiment":
            # Uncomment when implemented
            # runner = SentimentWorkflowRunner()
            logger.info("Sentiment model workflow not yet implemented")
            return
        elif model_name == "segmentation":
            # Uncomment when implemented
            # runner = SegmentationWorkflowRunner()
            logger.info("Segmentation model workflow not yet implemented")
            return
        elif model_name == "timeseries":
            # Uncomment when implemented
            # runner = TimeSeriesWorkflowRunner()
            logger.info("TimeSeries model workflow not yet implemented")
            return
        else:
            logger.error(f"Unknown model: {model_name}")
            return
            
        await runner.run()  
        
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<")

    except Exception as e:
        logger.exception(e)
        raise e

def main():
    """Main execution function with proper multiprocessing protection."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run ML pipeline for specific model')
    parser.add_argument('--model', type=str, default='churn',
                        choices=['churn', 'sentiment', 'segmentation', 'timeseries'],
                        help='Model to run pipeline for (default: churn)')
    args = parser.parse_args()
    
    # Run the async main function with the specified model
    asyncio.run(async_main(args.model))

if __name__ == '__main__':
    # Multiprocessing protection for Windows
    multiprocessing.freeze_support()
    
    # Run the main function
    main()
