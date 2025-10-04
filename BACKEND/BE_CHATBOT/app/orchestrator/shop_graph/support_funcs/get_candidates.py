from .supports import normalize_type
from qdrant_client import QdrantClient
import time
from qdrant_client.http import models

from config.base_config import APP_CONFIG
from utils.logging.logger import get_logger
logger = get_logger(__name__)

QDRANT_URL = APP_CONFIG.recommend_config.url
QDRANT_API_KEY = APP_CONFIG.recommend_config.api_key
COLLECTION = APP_CONFIG.recommend_config.collection_name

_cached_all_points = None
_cache_timestamp = 0
_client_cache = None
_CACHE_TTL = 300  # 5 minutes in seconds


def get_client():
    """Get cached Qdrant client to avoid repeated connections."""
    global _client_cache
    if _client_cache is None:
        _client_cache = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY.get_secret_value()
        )
    return _client_cache


def get_all_points(batch_size: int = 150, force_refresh: bool = False, device_type: str = "get_all") -> dict:
    """
    Retrieve all points from Qdrant, always returning a dictionary {type: points_list}.
    If type is 'get_all' or invalid, returns {"get_all": [...]} with no filtering.
    """
    global _cache_timestamp

    device_type = normalize_type(device_type)
    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > _CACHE_TTL

    try:
        client = get_client()
        if not hasattr(get_all_points, '_cache_by_type'):
            get_all_points._cache_by_type = {}

        cache_key = device_type
        if cache_key in get_all_points._cache_by_type and not cache_expired and not force_refresh:
            return {cache_key: get_all_points._cache_by_type[cache_key]}

        scroll_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.category",
                    match=models.MatchValue(value=device_type)
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

        get_all_points._cache_by_type[cache_key] = type_points
        _cache_timestamp = current_time
        print(f"Found {len(type_points)} points for category '{device_type}'")
        return {cache_key: type_points}

    except Exception as e:
        print(f"Error: {e}")
        return {device_type: get_all_points._cache_by_type.get(device_type, [])}
