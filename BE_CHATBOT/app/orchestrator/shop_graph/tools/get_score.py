from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List, Dict, Optional, Tuple
from qdrant_client import QdrantClient
import time
import joblib
import os
import numpy as np
from functools import lru_cache
from config.base_config import APP_CONFIG

QDRANT_URL = APP_CONFIG.recommend_config.url
QDRANT_API_KEY = APP_CONFIG.recommend_config.api_key
COLLECTION = APP_CONFIG.recommend_config.collection_name
KEYBERT = APP_CONFIG.key_bert_config.model

# Get the base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FALLBACK_MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "keybert.pkl")

# Global variables for caching
_vectorizer = None
_cached_all_points = None
_cache_timestamp = 0
_client_cache = None
_model_cache = None
_tfidf_matrix = None  # Cache TF-IDF matrix
_document_texts = None  # Cache document texts for TF-IDF
CACHE_DURATION = 300  # 5 minutes cache duration


def get_client():
    """Get cached Qdrant client to avoid repeated connections."""
    global _client_cache
    if _client_cache is None:
        _client_cache = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY.get_secret_value()
        )
    return _client_cache

@lru_cache(maxsize=1000)
def convert_to_string_cached(value) -> str:
    """Convert any value to a string with caching for repeated values."""
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value)

def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    # Use cached version for hashable types
    if isinstance(value, (str, int, float, bool, type(None))):
        return convert_to_string_cached(value)
    elif isinstance(value, (list, tuple)):
        # Convert to tuple for hashing if it's a list
        if isinstance(value, list):
            try:
                return convert_to_string_cached(tuple(value))
            except TypeError:
                # Fallback for unhashable items in list
                return " ".join(str(item) for item in value)
        return convert_to_string_cached(value)
    return str(value)


def check_similarity_vectorized(text1: str, point_indices: Optional[List[int]] = None) -> np.ndarray:
    """Vectorized similarity calculation using pre-computed TF-IDF matrix."""
    global _vectorizer, _tfidf_matrix
    
    if not text1 or _tfidf_matrix is None:
        return np.array([0.0])
    
    # Transform query text
    query_vector = _vectorizer.transform([text1])
    
    # Calculate similarities with specified points or all points
    if point_indices is not None:
        target_matrix = _tfidf_matrix[point_indices]
    else:
        target_matrix = _tfidf_matrix
    
    similarities = cosine_similarity(query_vector, target_matrix)[0]
    return similarities

def check_similarity(text1: str, texts: Optional[List[str]], vectorizer=None) -> float:
    """Legacy function maintained for backward compatibility."""
    if not text1 or not texts:
        return 0.0
    
    corpus = [text1] + texts
    
    if vectorizer is None:
        vectorizer = TfidfVectorizer(max_features=1000)  # Limit features for speed
        vectors = vectorizer.fit_transform(corpus)
    else:
        vectors = vectorizer.transform(corpus)
    
    similarities = cosine_similarity(vectors[0], vectors[1:])[0]
    return max(similarities) if similarities.size > 0 else 0.0

def get_all_points(batch_size: int = 500, force_refresh: bool = False):  # Increased batch size
    """Retrieve all points from Qdrant with improved caching and larger batches."""
    global _cached_all_points, _cache_timestamp, _tfidf_matrix
    
    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > CACHE_DURATION
    
    # Return cached results if valid and not forcing refresh
    if _cached_all_points is not None and not cache_expired and not force_refresh:
        return _cached_all_points
    
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
        
        _cached_all_points = all_points
        _cache_timestamp = current_time
        
        return _cached_all_points
        
    except Exception as e:
        print(f"Error retrieving points: {e}")
        return _cached_all_points if _cached_all_points is not None else []

def get_cached_model():
    """Get cached KeyBERT model to avoid repeated loading."""
    global _model_cache
    
    if _model_cache is not None:
        return _model_cache
    
    try:
        _model_cache = joblib.load(KEYBERT)
        print(f"[INFO] Loaded model from config: {KEYBERT}")
    except Exception as e:
        print(f"[WARN] Failed to load model from config: {e}")
        try:
            _model_cache = joblib.load(FALLBACK_MODEL_PATH)
            print(f"[INFO] Loaded fallback model from: {FALLBACK_MODEL_PATH}")
        except Exception as fallback_error:
            print(f"[ERROR] Failed to load fallback model: {fallback_error}")
            _model_cache = None
    
    return _model_cache

@lru_cache(maxsize=500)
def keyword_cached(user_query: str) -> str:
    """Cached version of keyword extraction for repeated queries."""
    return _keyword_extract(user_query)

def _keyword_extract(user_query: str) -> str:
    """Internal keyword extraction function."""
    model = get_cached_model()
    if model is None:
        return user_query

    try:
        keywords_with_scores = model.extract_keywords(
            user_query,
            keyphrase_ngram_range=(1, 2),
            stop_words=None,
            top_n=3,  # Reduced from 5 for speed
            use_mmr=True,
            diversity=0.5,
            seed_keywords=[
                "phone", "laptop", "pc", "earphone", "power bank", "mouse", "case", "keyboard",
                "apple", "xiaomi", "realme", "honor", "samsung", "oppo", "dell", "macbook",
                "msi", "asus", "hp", "lenovo", "acer", "gigabyte", "logitech", "marshall"
            ]
        )

        if not keywords_with_scores:
            return user_query

        return ", ".join([kw for kw, _ in keywords_with_scores])

    except Exception as e:
        print(f"[ERROR] Keyword extraction failed: {e}")
        return user_query

def keyword(user_query: str) -> str:
    """Extract keywords from user query with caching and error handling."""
    if not user_query or not user_query.strip():
        return ""
    
    return keyword_cached(user_query.strip())

# Batch processing functions for better performance
def batch_fuzzy_scoring(user_query: str, metadata_list: List[Dict]) -> List[float]:
    """Process multiple fuzzy scores in batch for better performance."""
    if not user_query:
        return [0.0] * len(metadata_list)
    
    user_query_lower = user_query.lower()
    scores = []
    
    for metadata in metadata_list:
        relevant_values = [
            convert_to_string(metadata[field]).lower() 
            for field in metadata 
            if field in metadata and metadata[field]
        ]
        
        if not relevant_values:
            scores.append(0.0)
        else:
            batch_scores = [fuzz.partial_ratio(user_query_lower, value) for value in relevant_values]
            scores.append(sum(batch_scores))
    
    return scores

def warm_up_cache():
    """Warm up all caches for better initial performance."""
    print("[INFO] Warming up caches...")
    
    # Load model cache
    get_cached_model()
    
    # Load points cache and build TF-IDF
    points = get_all_points()
    
    print(f"[INFO] Cache warmed up with {len(points)} points")

