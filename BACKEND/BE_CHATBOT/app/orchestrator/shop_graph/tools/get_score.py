from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List
from qdrant_client import QdrantClient
import time
from qdrant_client.http import models

from config.base_config import APP_CONFIG
from utils.logging.logger import get_logger
logger = get_logger(__name__)

QDRANT_URL = APP_CONFIG.recommend_config.url
QDRANT_API_KEY = APP_CONFIG.recommend_config.api_key
COLLECTION = APP_CONFIG.recommend_config.collection_name


# Global variables for caching
_vectorizer = None
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


def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)

def check_similarity(text1: str, combined_fields: List[str], vectorizer=None) -> float:
    """Calculate max cosine similarity between input and metadata fields."""
    global _vectorizer
    if not text1 or not combined_fields:
        return 0.0

    corpus = [text1] + combined_fields
    if vectorizer is None:
        if _vectorizer is None:
            _vectorizer = TfidfVectorizer().fit(corpus)
        vectorizer = _vectorizer

    vectors = vectorizer.transform(corpus)
    similarities = cosine_similarity(vectors[0], vectors[1:])[0]
    return max(similarities) if similarities.size > 0 else 0.0
def get_all_points(batch_size: int = 150, force_refresh: bool = False, type: str = None):
    """Retrieve all points from Qdrant. If type is invalid or None, scroll without filtering."""
    global _cache_timestamp
    type = type.lower() if type else None

    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > _CACHE_TTL

    valid_types = {"phone", "laptop/pc", "earphone", "mouse", "keyboard"}
    is_valid_type = type in valid_types
    cache_key = type if is_valid_type else "all"

    if (hasattr(get_all_points, '_cache_by_type') and 
        cache_key in get_all_points._cache_by_type and 
        not cache_expired and not force_refresh):
        return get_all_points._cache_by_type[cache_key]

    try:
        client = get_client()
        offset = None
        all_points = []

        scroll_filter = None
        if is_valid_type:
            scroll_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.category",
                        match=models.MatchValue(value=type)
                    )
                ]
            )

        while True:
            points, offset = client.scroll(
                collection_name="FPT_SHOP",
                scroll_filter=scroll_filter,
                with_vectors=False,
                with_payload=True,
                limit=batch_size,
                offset=offset
            )

            all_points.extend(points)

            if not points or offset is None:
                break

        if not hasattr(get_all_points, '_cache_by_type'):
            get_all_points._cache_by_type = {}

        get_all_points._cache_by_type[cache_key] = all_points
        _cache_timestamp = current_time

        if is_valid_type:
            logger.info(f"Found {len(all_points)} points with category '{type}'")
        else:
            logger.info(f"Invalid or missing category '{type}', returning all {len(all_points)} points")

        return all_points

    except Exception as e:
        logger.info(f"Error: {e}")
        if (hasattr(get_all_points, '_cache_by_type') and 
            cache_key in get_all_points._cache_by_type):
            return get_all_points._cache_by_type[cache_key]
        return []