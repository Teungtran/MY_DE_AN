from typing import Optional, Dict, Tuple, List 
import time
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
