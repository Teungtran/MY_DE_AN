from typing import Dict, Tuple, Optional
import time
from datetime import datetime

# Cache for storing URL content
url_content_cache: Dict[str, Tuple[str, str, float]] = {}

# Cache expiration time in seconds (default: 1 hour)
CACHE_EXPIRATION = 600
def store_url_content(url: str, content: str, original_query: str) -> None:
    """
    Store URL content in cache with timestamp
    
    Args:
        url: The URL that was crawled
        content: The extracted content from the URL
        original_query: The original user query that triggered this crawl
    """
    url_content_cache[url] = (content, original_query, time.time())

def get_url_content(url: str) -> Optional[Tuple[str, str, float]]:
    """
    Retrieve URL content from cache if it exists and hasn't expired
    
    Args:
        url: The URL to retrieve content for
        
    Returns:
        Tuple of (content, original_query, timestamp) if found and valid, None otherwise
    """
    if url in url_content_cache:
        content, query, timestamp = url_content_cache[url]
        if time.time() - timestamp < CACHE_EXPIRATION:
            return content, query, timestamp
    return None

def get_all_cached_urls() -> Dict[str, Tuple[str, datetime]]:
    """
    Get all cached URLs with their original queries and cache timestamps
    
    Returns:
        Dictionary mapping URLs to tuples of (original_query, datetime)
    """
    result = {}
    for url, (_, query, timestamp) in url_content_cache.items():
        result[url] = (query, datetime.fromtimestamp(timestamp))
    return result

def clear_expired_cache() -> int:
    """
    Clear expired entries from cache
    
    Returns:
        Number of entries cleared
    """
    expired_keys = []
    current_time = time.time()
    
    for url, (_, _, timestamp) in url_content_cache.items():
        if current_time - timestamp > CACHE_EXPIRATION:
            expired_keys.append(url)
            
    for key in expired_keys:
        del url_content_cache[key]
        
    return len(expired_keys)

def get_combined_content(urls: list[str]) -> Tuple[str, list[str]]:
    """
    Get combined content from multiple cached URLs
    
    Args:
        urls: List of URLs to retrieve and combine content from
        
    Returns:
        Tuple of (combined content, list of URLs that were found in cache)
    """
    combined_content = []
    found_urls = []
    
    for url in urls:
        cached = get_url_content(url)
        if cached:
            content, _, _ = cached
            combined_content.append(f"Content from {url}:\n{content}")
            found_urls.append(url)
            
    if not combined_content:
        return "", []
        
    return "\n\n---\n\n".join(combined_content), found_urls 