import redis
from app.config.base_config import APP_CONFIG
from app.utils.logging.logger import get_logger
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
            logger.debug(f"Redis connection check successful - reusing existing connection to {REDIS_HOST}:11899")
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection lost to {REDIS_HOST}:11899, attempting to reconnect... Error: {e}")
            _redis_client = None
    
    # Log connection attempt
    logger.info(f"Attempting to connect to Redis at {REDIS_HOST}:11899...")
    
    try:
        # Create connection pool with proper settings
        pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=11899,
            password=REDIS_PASS,
            max_connections=50,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        logger.debug(f"Redis connection pool created for {REDIS_HOST}:11899 with max_connections=50")
        
        _redis_client = redis.Redis(connection_pool=pool, username="default")
        
        # Test the connection
        _redis_client.ping()
        logger.info(f"Redis connection established successfully to {REDIS_HOST}:11899 with connection pooling (max_connections=50, health_check_interval=30s)")
        return _redis_client
        
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection failed to {REDIS_HOST}:11899 - ConnectionError: {e}")
        return None
    except redis.exceptions.TimeoutError as e:
        logger.error(f"Redis connection timeout to {REDIS_HOST}:11899 - TimeoutError: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis at {REDIS_HOST}:11899: {type(e).__name__}: {e}")
        return None