import os
import sys
import multiprocessing
import uvicorn
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("backend_launcher")

def run_admin_service():
    """Run the BE_ADMIN FastAPI service"""
    logger.info("Starting BE_ADMIN service...")
    
    # Add BE_ADMIN to path for imports
    admin_path = os.path.join(os.path.dirname(__file__), 'BE_ADMIN')
    sys.path.insert(0, admin_path)
    
    # Run the admin service
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8091, 
        reload=False,
        log_level="info",
        app_dir=admin_path
    )

def run_chatbot_service():
    """Run the BE_CHATBOT FastAPI service"""
    logger.info("Starting BE_CHATBOT service...")
    
    # Add BE_CHATBOT to path for imports
    chatbot_path = os.path.join(os.path.dirname(__file__), 'BE_CHATBOT')
    sys.path.insert(0, chatbot_path)
    
    # Run the chatbot service
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8090, 
        reload=False,
        log_level="info",
        app_dir=chatbot_path
    )

def run_preprocess_service():
    """Run the BE_PREPROCESS FastAPI service"""
    logger.info("Starting BE_PREPROCESS service...")
    
    # Add BE_PREPROCESS to path for imports
    preprocess_path = os.path.join(os.path.dirname(__file__), 'BE_PREPROCESS')
    sys.path.insert(0, preprocess_path)
    
    # Run the preprocess service
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8092, 
        reload=False,
        log_level="info",
        app_dir=preprocess_path
    )

if __name__ == "__main__":
    logger.info("Starting all backend services...")
    
    # Create processes for each service
    admin_process = multiprocessing.Process(target=run_admin_service)
    chatbot_process = multiprocessing.Process(target=run_chatbot_service)
    preprocess_process = multiprocessing.Process(target=run_preprocess_service)
    
    # Start all processes
    admin_process.start()
    chatbot_process.start()
    preprocess_process.start()
    
    try:
        # Wait for all processes to complete (which they won't unless terminated)
        admin_process.join()
        chatbot_process.join()
        preprocess_process.join()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down services...")
        
        # Terminate processes
        admin_process.terminate()
        chatbot_process.terminate()
        preprocess_process.terminate()
        
        # Wait for processes to terminate
        admin_process.join()
        chatbot_process.join()
        preprocess_process.join()
        
        logger.info("All services have been shut down.")
