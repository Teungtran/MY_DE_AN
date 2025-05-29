from langgraph.checkpoint.mongodb import MongoDBSaver
from config.base_config import APP_CONFIG
from utils.logging.logger import get_logger
MONGO_DB_URL = APP_CONFIG.mongo_config.url
logger = get_logger(__name__)

def test_mongo_connection(mongo_url):
    """Test MongoDB connection before using it."""
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_url)
        client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {str(e)}")
        return False

from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

def create_checkpointer():
    status  = test_mongo_connection(MONGO_DB_URL)
    if not status:
        return None
    client = MongoClient(MONGO_DB_URL)

    # Create checkpointer directly
    checkpointer = MongoDBSaver(
        client=client,
        database_name="langgraph",
        collection_name="checkpoints"
    )

    if hasattr(checkpointer, "setup"):
        checkpointer.setup()

    return checkpointer