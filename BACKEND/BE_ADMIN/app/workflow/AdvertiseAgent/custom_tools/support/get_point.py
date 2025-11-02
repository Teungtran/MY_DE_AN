
from qdrant_client import QdrantClient
import time
from qdrant_client.http import models
from pydantic import SecretStr
from app.config.base_config import APP_CONFIG
from app.utils.logging.logger import get_logger
logger = get_logger(__name__)
QDRANT_URL = APP_CONFIG.recommend_config.url
QDRANT_API_KEY = APP_CONFIG.recommend_config.api_key
COLLECTION = APP_CONFIG.recommend_config.collection_name
_cache_timestamp = 0
_client_cache = None
_CACHE_TTL = 300 
_cache_by_type = {}  # Use module-level dict instead of function attribute

def get_client():
    """Get cached Qdrant client to avoid repeated connections."""
    global _client_cache
    if _client_cache is None:
        # Convert SecretStr to string if needed
        api_key = QDRANT_API_KEY
        if isinstance(api_key, SecretStr):
            api_key = api_key.get_secret_value()
        
        _client_cache = QdrantClient(
            url=QDRANT_URL,
            api_key=api_key
        )
    return _client_cache

def get_all_points(batch_size: int = 150, force_refresh: bool = False, type: str = "get_all") -> dict:
    """
    Retrieve all points from Qdrant, always returning a dictionary {type: points_list}.
    If type is 'get_all' or invalid, returns {"get_all": [...]} with no filtering.
    """
    global _cache_timestamp

    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > _CACHE_TTL

    valid_types = {"phone", "laptop/pc", "tablet"}
    is_get_all = type == "get_all" or type not in valid_types


    if is_get_all:
        cache_key = "get_all"
        if (cache_key in _cache_by_type and 
            not cache_expired and not force_refresh):
            return {cache_key: _cache_by_type[cache_key]}

        try:
            client = get_client()
            offset = None
            all_points = []
            while True:
                points, offset = client.scroll(
                    collection_name=COLLECTION,
                    scroll_filter=None,
                    with_vectors=False,
                    with_payload=True,
                    limit=batch_size,
                    offset=offset
                )
                all_points.extend(points)
                if not points or offset is None:
                    break

            _cache_by_type[cache_key] = all_points
            _cache_timestamp = current_time
            logger.info(f"Returning {len(all_points)} total points (no category filter)")
            return {cache_key: all_points}

        except Exception as e:
            logger.error(f"Error: {e}")
            return {cache_key: _cache_by_type.get(cache_key, [])}

    try:
        client = get_client()
        cache_key = type
        if cache_key in _cache_by_type and not cache_expired and not force_refresh:
            return {cache_key: _cache_by_type[cache_key]}

        scroll_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.category",
                    match=models.MatchValue(value=type)
                )
            ]
        )

        offset = None
        type_points = []
        while True:
            points, offset = client.scroll(
                collection_name=COLLECTION,
                scroll_filter=scroll_filter,
                with_vectors=False,
                with_payload=True,
                limit=batch_size,
                offset=offset
            )
            type_points.extend(points)
            if not points or offset is None:
                break

        _cache_by_type[cache_key] = type_points
        _cache_timestamp = current_time
        logger.info(f"Found {len(type_points)} points for category '{type}'")
        return {cache_key: type_points}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {type: _cache_by_type.get(type, [])}