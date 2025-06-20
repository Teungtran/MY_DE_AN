from config.base_config import APP_CONFIG
from utils.logging.logger import get_logger
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from typing import Optional

MONGO_DB_URL = APP_CONFIG.mongo_config.url
logger = get_logger(__name__)

# Global MongoDB client singleton
_mongo_client: Optional[MongoClient] = None
_checkpointer: Optional[MongoDBSaver] = None

def get_mongo_client() -> Optional[MongoClient]:
    """Get or create singleton MongoDB client with connection pooling."""
    global _mongo_client
    
    if _mongo_client is not None:
        try:
            # Quick health check
            _mongo_client.admin.command('ping')
            return _mongo_client
        except Exception as e:
            logger.warning(f"MongoDB connection lost: {e}, attempting to reconnect...")
            _mongo_client = None
    
    try:
        # Create client with connection pooling
        _mongo_client = MongoClient(
            MONGO_DB_URL,
            maxPoolSize=100,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            retryWrites=True,
            retryReads=True
        )
        _mongo_client.admin.command('ping')
        logger.info("MongoDB client initialized with connection pooling")
        return _mongo_client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return None


def create_checkpointer() -> Optional[MongoDBSaver]:
    """Create or get existing MongoDB checkpointer."""
    global _checkpointer
    
    if _checkpointer is not None:
        return _checkpointer
    
    client = get_mongo_client()
    if not client:
        return None

    # Create checkpointer directly
    _checkpointer = MongoDBSaver(client=client)

    if hasattr(_checkpointer, "setup"):
        _checkpointer.setup()

    return _checkpointer