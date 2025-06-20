import redis
from config.base_config import APP_CONFIG
from utils.logging.logger import get_logger

logger = get_logger(__name__)
REDIS_PASS = APP_CONFIG.redis_config.password
REDIS_HOST = APP_CONFIG.redis_config.host

def redis_caching():
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=16594,
            password=REDIS_PASS,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test the connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
        return redis_client
        
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        return None