from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
import time
import joblib
import os
from config.base_config import APP_CONFIG

QDRANT_URL = APP_CONFIG.recommend_config.url
QDRANT_API_KEY = APP_CONFIG.recommend_config.api_key
COLLECTION = APP_CONFIG.recommend_config.collection_name
KEYBERT = APP_CONFIG.key_bert_config.model
FALLBACK_MODEL_PATH = r"C:\Users\Admin\Desktop\DE_AN\BE_CHATBOT\saved_models\keybert.pkl"

# Global variables for caching
_vectorizer = None
_cached_all_points = None
_cache_timestamp = 0
_client_cache = None
_model_cache = None
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

def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)

def fuzzy_score(user_query: str, metadata: Dict) -> float:
    """Calculate enhanced fuzzy matching score using multiple algorithms."""
    if not user_query:
        return 0.0
    
    user_query_lower = user_query.lower()
    priority_fields = ['device_name','brand','category','discount_percent', 'sales_perks',
                    'payment_perks','sales_price']
    
    # Use sum with generator for better performance
    fuzzy_sim = sum(
        fuzz.partial_ratio(user_query_lower, convert_to_string(metadata.get(field, "")).lower())
        for field in priority_fields if field in metadata
    )
    return fuzzy_sim

def check_similarity(text1: str, texts: Optional[List[str]], vectorizer=None) -> float:
    """Calculate max cosine similarity between text1 and a list of strings. Optionally reuse a vectorizer."""
    global _vectorizer
    
    if not text1 or not texts:
        return 0.0
    
    corpus = [text1] + texts
    
    # Reuse global vectorizer if possible
    if vectorizer is None:
        if _vectorizer is None:
            _vectorizer = TfidfVectorizer().fit(corpus)
            vectorizer = _vectorizer
        else:
            vectorizer = _vectorizer
    
    vectors = vectorizer.transform(corpus)
    similarities = cosine_similarity(vectors[0], vectors[1:])[0]
    return max(similarities) if similarities.size > 0 else 0.0

def get_all_points(batch_size: int = 100, force_refresh: bool = False):
    """Retrieve all points from Qdrant with improved caching strategy."""
    global _cached_all_points, _cache_timestamp
    
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

def keyword(user_query: str) -> str:
    """Extract keywords from user query with error handling and fallback support."""
    if not user_query or not user_query.strip():
        return ""

    model = get_cached_model()
    if model is None:
        return user_query

    try:
        keywords_with_scores = model.extract_keywords(
            user_query,
            keyphrase_ngram_range=(1, 2),
            stop_words=None,
            top_n=5,
            use_mmr=True,
            diversity=0.5,
            seed_keywords=[
                "phone", "laptop/pc", "earphone", "power bank", "mouse", "case", "keyboard",
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