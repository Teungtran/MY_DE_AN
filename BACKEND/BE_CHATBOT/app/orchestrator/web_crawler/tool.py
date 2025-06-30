from .llm import get_context
from .url import URLCrawler
from .cache import store_url_content,  get_combined_content, get_all_cached_urls, clear_expired_cache
from schemas.device_schemas import UrlExtraction
import warnings
warnings.filterwarnings('ignore')
from langchain_core.tools import tool
import asyncio
from typing import List

@tool("url_extraction", args_schema=UrlExtraction)
def url_extraction(user_input: str, urls: List[str]) -> str:
    """
    Extracts information from one or more URLs based on user input.
    
    Args:
        user_input: The user's question about the URL content
        url: A single URL string or a list of URL strings to extract information from
        
    Returns:
        The extracted information as a string
    """
    crawler = URLCrawler()
    all_content = []
    for single_url in urls:
        try:
            # Crawl the URL
            content, _ = asyncio.run(crawler.get_converted_document(single_url))
            if content:
                all_content.append(f"Content from {single_url}:\n{content}")
                store_url_content(single_url, content, user_input)
        except Exception as e:
            all_content.append(f"Error extracting content from {single_url}: {str(e)}")
    
    # Combine all content
    combined_content = "\n\n---\n\n".join(all_content)
    
    # If no content was retrieved
    if not combined_content:
        return "Unable to extract content from the provided URL(s). Please check if the URLs are valid."
    
    answer = get_context(combined_content, user_input)
    return answer

@tool("url_followup")
def url_followup(user_input: str) -> str:
    """
    Answers follow-up questions using previously cached URL content.
    Use this tool when the user asks a question about URLs they've previously viewed.
    No need to provide URLs - it will use all cached content.
    
    Args:
        user_input: The user's follow-up question about previously viewed URL content
        
    Returns:
        The answer to the follow-up question based on cached content
    """
    clear_expired_cache()
    
    cached_urls = get_all_cached_urls()
    
    if not cached_urls:
        return "No previously viewed URL content is available. Please provide a URL to extract information from."
    
    all_urls = list(cached_urls.keys())
    combined_content, _ = get_combined_content(all_urls)
    
    if not combined_content:
        return "Unable to retrieve cached content. Please provide a URL to extract fresh information."
    
    answer = get_context(combined_content, user_input)
    return answer

