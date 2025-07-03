from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz.fuzz import partial_ratio
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

def calculate_similarities_batch(main_query: str, candidates: list, field: str) -> dict:
    """Calculate similarities for all candidates at once."""
    field_values = []
    candidate_ids = []
    
    for i, candidate in enumerate(candidates):
        meta = candidate["doc"].payload.get("metadata", {})
        field_value = convert_to_string(meta.get(field, ""))
        field_values.append(field_value if field_value else "")
        candidate_ids.append(i)
    
    if not field_values:
        return {i: 0.0 for i in candidate_ids}
    
    corpus = [main_query] + field_values
    vectorizer = TfidfVectorizer()
    
    try:
        vectors = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(vectors[0], vectors[1:])[0]
        return {candidate_ids[i]: float(similarities[i]) for i in range(len(candidate_ids))}
    except Exception as e:
        print(f"Similarity calculation failed: {e}")
        return {i: 0.0 for i in candidate_ids}
    
def get_all_points(batch_size: int = 150, force_refresh: bool = False, type: str = "get_all") -> dict:
    """
    Retrieve all points from Qdrant, always returning a dictionary {type: points_list}.
    If type is 'get_all' or invalid, returns {"get_all": [...]} with no filtering.
    """
    global _cache_timestamp

    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > _CACHE_TTL

    valid_types = {"phone", "laptop/pc", "earphone", "mouse", "keyboard"}
    is_get_all = type == "get_all" or type not in valid_types


    if is_get_all:
        cache_key = "get_all"
        if (hasattr(get_all_points, '_cache_by_type') and 
            cache_key in get_all_points._cache_by_type and 
            not cache_expired and not force_refresh):
            return {cache_key: get_all_points._cache_by_type[cache_key]}

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
                if not points or offset is None:
                    break

            if not hasattr(get_all_points, '_cache_by_type'):
                get_all_points._cache_by_type = {}

            get_all_points._cache_by_type[cache_key] = all_points
            _cache_timestamp = current_time
            print(f"Returning {len(all_points)} total points (no category filter)")
            return {cache_key: all_points}

        except Exception as e:
            print(f"Error: {e}")
            return {cache_key: get_all_points._cache_by_type.get(cache_key, [])}

    # Handle valid specific type
    try:
        client = get_client()
        if not hasattr(get_all_points, '_cache_by_type'):
            get_all_points._cache_by_type = {}

        cache_key = type
        if cache_key in get_all_points._cache_by_type and not cache_expired and not force_refresh:
            return {cache_key: get_all_points._cache_by_type[cache_key]}

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
                collection_name="FPT_SHOP",
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
        print(f"Found {len(type_points)} points for category '{type}'")
        return {cache_key: type_points}

    except Exception as e:
        print(f"Error: {e}")
        return {type: get_all_points._cache_by_type.get(type, [])}

import random
def determine_field_relevance(query: str, all_points: list, text_fields: list) -> list:
    """
    Determine which fields are most relevant to the user query.
    Returns list of (field_name, relevance_score) tuples sorted by relevance.
    """
    field_relevance = {}
    
    for field in text_fields:
        sample_size = min(50, len(all_points))
        sample_docs = random.sample(all_points, sample_size)
        
        field_scores = []
        for doc in sample_docs:
            meta = doc.payload.get("metadata", {})
            field_value = convert_to_string(meta.get(field, ""))
            
            if field_value:
                score = partial_ratio(query, field_value.lower())
                field_scores.append(score)
        
        if field_scores:
            avg_relevance = sum(field_scores) / len(field_scores)
            field_relevance[field] = avg_relevance
        else:
            field_relevance[field] = 0
    
    return sorted(field_relevance.items(), key=lambda x: x[1], reverse=True)