import redis
from config.base_config import APP_CONFIG
from utils.logging.logger import get_logger
from typing import Optional

logger = get_logger(__name__)
REDIS_PASS = APP_CONFIG.redis_config.password
REDIS_HOST = APP_CONFIG.redis_config.host

# Global singleton instance
_redis_client: Optional[redis.Redis] = None

def redis_caching() -> Optional[redis.Redis]:
    """
    Get or create a singleton Redis client with connection pooling.
    This prevents creating multiple connections and improves performance.
    """
    global _redis_client
    
    if _redis_client is not None:
        try:
            # Quick health check
            _redis_client.ping()
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis connection lost, attempting to reconnect...")
            _redis_client = None
    
    try:
        # Create connection pool with proper settings
        pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=16594,
            password=REDIS_PASS,
            max_connections=50,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        _redis_client = redis.Redis(connection_pool=pool)
        
        # Test the connection
        _redis_client.ping()
        logger.info("Redis connection established successfully with connection pooling")
        return _redis_client
        
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        return None