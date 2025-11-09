from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from app.utils.cleaning import count_words
from app.config.base_config import APP_CONFIG
import time
from typing import Dict, List, Optional, Tuple
from app.factories.embedding_factory import create_embedding_model
embedding_model = create_embedding_model(APP_CONFIG.embedding_model_config)

# Global persistent FAISS store and chunk tracking
_global_faiss_store = None
_chunk_metadata: List[Tuple[Document, float]] = []  # (document, timestamp)
FAISS_CHUNK_THRESHOLD = 200  # Maximum number of chunks before cleanup (adjust based on your needs)

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

def _cleanup_old_chunks():
    """
    Remove the oldest half of chunks from FAISS when threshold is reached
    """
    global _global_faiss_store, _chunk_metadata
    
    if len(_chunk_metadata) <= FAISS_CHUNK_THRESHOLD:
        return
    
    print(f"[DEBUG] FAISS cleanup triggered: {len(_chunk_metadata)} chunks exceed threshold {FAISS_CHUNK_THRESHOLD}")
    
    # Sort by timestamp (oldest first)
    _chunk_metadata.sort(key=lambda x: x[1])
    
    # Calculate how many to remove (half)
    num_to_remove = len(_chunk_metadata) // 2
    
    # Keep the newer half
    chunks_to_keep = _chunk_metadata[num_to_remove:]
    documents_to_keep = [doc for doc, _ in chunks_to_keep]
    
    print(f"[DEBUG] Removing {num_to_remove} oldest chunks, keeping {len(documents_to_keep)} newest chunks")
    
    # Recreate FAISS store with only the newer chunks
    if documents_to_keep:
        _global_faiss_store = FAISS.from_documents(documents_to_keep, embedding_model)
        _chunk_metadata = chunks_to_keep
        print(f"[DEBUG] FAISS store recreated with {len(documents_to_keep)} chunks")
    else:
        _global_faiss_store = None
        _chunk_metadata = []
        print("[DEBUG] FAISS store cleared (no chunks remaining)")

def create_temporary_faiss_store(top_matches):
    """
    Add new chunks to persistent FAISS store with threshold-based cleanup
    """
    global _global_faiss_store, _chunk_metadata
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    
    page_documents = []
    current_time = time.time()

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

    if not page_documents:
        print("[DEBUG] No new documents to add to FAISS")
        return _global_faiss_store
    
    print(f"[DEBUG] Adding {len(page_documents)} new chunks to FAISS store")
    
    # Add timestamp metadata to new documents
    for doc in page_documents:
        _chunk_metadata.append((doc, current_time))
    
    # Create or update FAISS store
    if _global_faiss_store is None:
        print("[DEBUG] Creating new FAISS store")
        _global_faiss_store = FAISS.from_documents(page_documents, embedding_model)
    else:
        print(f"[DEBUG] Adding to existing FAISS store (current size: {len(_chunk_metadata) - len(page_documents)} chunks)")
        # Add new documents to existing store
        _global_faiss_store.add_documents(page_documents)
    
    print(f"[DEBUG] FAISS store now has {len(_chunk_metadata)} total chunks")
    
    # Check if cleanup is needed
    _cleanup_old_chunks()
    
    return _global_faiss_store
    
    
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

def clear_faiss_store() -> None:
    """
    Manually clear the entire FAISS store and chunk metadata
    Useful for testing or manual cleanup
    """
    global _global_faiss_store, _chunk_metadata
    _global_faiss_store = None
    _chunk_metadata = []
    print("[DEBUG] FAISS store manually cleared")

def get_faiss_store_info() -> Dict[str, any]:
    """
    Get information about the current FAISS store
    
    Returns:
        Dictionary with store statistics
    """
    global _global_faiss_store, _chunk_metadata
    return {
        "total_chunks": len(_chunk_metadata),
        "threshold": FAISS_CHUNK_THRESHOLD,
        "store_exists": _global_faiss_store is not None,
        "chunks_until_cleanup": max(0, FAISS_CHUNK_THRESHOLD - len(_chunk_metadata))
    }
