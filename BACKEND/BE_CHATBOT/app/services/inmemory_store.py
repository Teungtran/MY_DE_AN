from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from app.utils.cleaning import count_words
from app.config.base_config import APP_CONFIG
import time
from typing import Dict, List, Optional, Tuple
from app.factories.embedding_factory import create_embedding_model
embedding_model = create_embedding_model(APP_CONFIG.embedding_model_config)

def merge_small_chunks(chunks, min_words=150):
    if not chunks:
        return []

    merged_chunks = [chunks[0]]
    
    for chunk in chunks[1:]:
        if count_words(chunk.page_content) < min_words:
            # Merge with previous
            merged_chunks[-1].page_content += " " + chunk.page_content
        else:
            merged_chunks.append(chunk)

    return merged_chunks
def create_temporary_faiss_store(top_matches):
    """
    Always create a completely fresh FAISS store (guaranteed clean)
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    
    page_documents = []

    for item in top_matches:
        try:
            # Handle both dict and direct doc object formats
            if isinstance(item, dict) and "doc" in item:
                doc_obj = item["doc"]
            else:
                doc_obj = item
                
            payload = doc_obj.payload
            page_content = payload.get("page_content") or payload.get("metadata", {}).get("page_content")
            if page_content:
                chunks = text_splitter.create_documents([page_content])
                merged_chunks = merge_small_chunks(chunks)
                page_documents.extend(merged_chunks)
        except Exception as e:
            print(f"[DEBUG] Error processing item for FAISS: {e}")
            continue

    if page_documents:
        faiss_store = FAISS.from_documents(page_documents, embedding_model)
        return faiss_store
    else:
        return None
    
    
recommended_devices_cache: Dict[str, Tuple[List[str], str, float]] = {}
CACHE_EXPIRATION = 900

def store_recommended_devices(devices: List[str], original_query: str) -> None:
    """
    Store recommended devices in cache with timestamp
    
    Args:
        devices: List of recommended device names
        original_query: The original user query that triggered this recommendation
    """
    cache_key = "latest_recommendations"
    recommended_devices_cache[cache_key] = (devices, original_query, time.time())

def get_recommended_devices() -> Optional[Tuple[List[str], str, float]]:
    """
    Retrieve recommended devices from cache if they exist and haven't expired
    
    Returns:
        Tuple of (devices_list, original_query, timestamp) if found and valid, None otherwise
    """
    cache_key = "latest_recommendations"
    if cache_key in recommended_devices_cache:
        devices, query, timestamp = recommended_devices_cache[cache_key]
        if time.time() - timestamp < CACHE_EXPIRATION:
            return devices, query, timestamp
    return None



def clear_expired_recommendations() -> int:
    """
    Clear expired entries from recommendations cache
    
    Returns:
        Number of entries cleared
    """
    expired_keys = []
    current_time = time.time()
    
    for cache_key, (_, _, timestamp) in recommended_devices_cache.items():
        if current_time - timestamp > CACHE_EXPIRATION:
            expired_keys.append(cache_key)
            
    for key in expired_keys:
        del recommended_devices_cache[key]
        
    return len(expired_keys)
