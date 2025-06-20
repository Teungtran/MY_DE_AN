from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List
from qdrant_client import QdrantClient
import time

from config.base_config import APP_CONFIG
from pathlib import Path

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

def fuzzy_score(user_query: str, combined_text: str) -> float:
    """Compute fuzzy score against a single combined metadata string."""
    if not user_query or not combined_text:
        return 0.0
    return fuzz.partial_ratio(user_query.lower(), combined_text.lower())

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
def get_all_points(batch_size: int = 100, force_refresh: bool = False):
    """Retrieve all points from Qdrant with improved caching strategy."""
    global _cached_all_points, _cache_timestamp
    
    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > _CACHE_TTL
    
    if _cached_all_points is not None and not cache_expired and not force_refresh:
        return _cached_all_points
    
    try:
        client = get_client()
        offset = None
        all_points = []
        
        while True:
            points, offset = client.scroll(
                collection_name="FPT_SHOP",
                scroll_filter=None,
                with_vectors=False,
                with_payload=True,
                limit=batch_size,
                offset=offset
            )
            
            all_points.extend(points)
            
            # If no more results or offset is None, break
            if not points or offset is None:
                break
        
        _cached_all_points = all_points
        _cache_timestamp = current_time
        return _cached_all_points
        
    except Exception as e:
        return _cached_all_points if _cached_all_points is not None else []

