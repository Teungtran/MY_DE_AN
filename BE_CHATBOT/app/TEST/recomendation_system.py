from qdrant_client import QdrantClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List, Dict, Optional, Any, Tuple, Union
from langdetect import detect
import functools
import re
from dataclasses import dataclass
from enum import Enum
# Configuration constants
AZURE_OPENAI_API_KEY="4QwaRjqSZ4i4nwy32W0MpDS1oYrGiwbD3A4HjyEIIquptvRZ5qDHJQQJ99BBACHYHv6XJ3w3AAAAACOGCSqn"
AZURE_OPENAI_ENDPOINT="https://fhna-m71ldg7w-eastus2.openai.azure.com"
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
QDRANT_URL = "https://84ff8fdd-082b-4d65-b876-08ac97d56f79.us-west-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.EfXJxIIYMTdtWmLju3V5PobzwP61mE1IWxlWXZUxh1k"
QDRANT_COLLECTION_NAME = "FPT_Knowledge_base"

# Initialize Qdrant client once
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)
class RecommendationConfig:
    MIN_MATCH_SCORE = 70.0
    MAX_RESULTS = 5
    FUZZY_WEIGHT = 0.5
    COSINE_WEIGHT = 0.5
    HISTORY_BRAND_BOOST = 10.0
    HISTORY_STORAGE_BOOST = 8.0
    HISTORY_COLOR_BOOST = 5.0
    BRAND_SIMILARITY_THRESHOLD = 0.3
    BRAND_MATCH_BOOST = 10.0
    PRICE_RANGE_MATCH_BOOST = 10.0

    @classmethod
    def create_custom_config(cls, **kwargs):
        """Create a custom configuration with specified overrides.
        
        Args:
            **kwargs: Key-value pairs to override default config values
            
        Returns:
            A new RecommendationConfig instance with custom values
        """
        config = cls()
        for key, value in kwargs.items():
            if hasattr(config, key.upper()):
                setattr(config, key.upper(), value)
            else:
                print(f"Warning: Unknown config parameter '{key}'")
        return config


class ProductFieldImportance(Enum):
    """Define importance weights for different product fields"""
    HIGH = 2.0    # Critical product attributes
    MEDIUM = 1.0  # Important but not decisive 
    LOW = 0.5     # Supplementary information

FIELD_WEIGHTS = {
    'device_name': ProductFieldImportance.HIGH.value,
    'cpu': ProductFieldImportance.MEDIUM.value,
    'card': ProductFieldImportance.MEDIUM.value,
    'screen': ProductFieldImportance.MEDIUM.value,
    'suitable_for': ProductFieldImportance.HIGH.value,
    'storage': ProductFieldImportance.HIGH.value,
    'colors': ProductFieldImportance.LOW.value,
    'sale_price': ProductFieldImportance.HIGH.value,
    'guarantee_program': ProductFieldImportance.LOW.value,
    'payment_perks': ProductFieldImportance.LOW.value,
    'discount_percent': ProductFieldImportance.MEDIUM.value
}

def create_custom_weights(base_weights: Dict[str, float] = None, **kwargs) -> Dict[str, float]:
    """
    Create custom field weights by overriding default weights.
    
    Args:
        base_weights: Base weights to start with (defaults to FIELD_WEIGHTS)
        **kwargs: Field-weight pairs to override
        
    Returns:
        Dictionary of field weights with customized values
    """
    weights = base_weights.copy() if base_weights else FIELD_WEIGHTS.copy()
    
    # Update weights with custom values
    for field, weight in kwargs.items():
        weights[field] = weight
        
    return weights

@functools.lru_cache(maxsize=1)
def ai_model():
    return AzureChatOpenAI(
        openai_api_key=AZURE_OPENAI_API_KEY,
        openai_api_version=AZURE_OPENAI_API_VERSION,
        model="gpt-4o-mini",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        temperature=0
    )

def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)

def fuzzy_score(user_query: str, metadata: Dict, field_weights: Dict[str, float] = None) -> float:
    """Calculate fuzzy matching score between user query and metadata."""
    user_query_lower = user_query.lower()
    score = 0
    
    weights = field_weights or FIELD_WEIGHTS
    
    for field, weight in weights.items():
        if field in metadata and metadata[field]:
            value_str = convert_to_string(metadata[field])
            field_score = fuzz.partial_ratio(user_query_lower, value_str.lower())
            score += field_score * weight
    
    return score / sum(weights.values()) * 100

def check_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two text strings."""
    vectorizer = CountVectorizer().fit([text1, text2])
    vectors = vectorizer.transform([text1, text2])
    return cosine_similarity(vectors[0], vectors[1])[0][0]

def cosine_score(user_query: str, metadata: Dict, field_weights: Dict[str, float] = None) -> float:
    """Calculate cosine similarity score between user query and metadata."""
    # Use provided field weights or defaults
    weights = field_weights or FIELD_WEIGHTS
    
    # Use only fields defined in weights
    features = []
    feature_weights = []
    
    for field, weight in weights.items():
        if field in metadata and metadata[field]:
            field_text = convert_to_string(metadata[field])
            features.append(field_text)
            feature_weights.append(weight)
    
    if not features:
        return 0
    
    # Weight the features according to their importance
    metadata_text = " ".join(features)
    vectorizer = CountVectorizer().fit([user_query, metadata_text])
    vectors = vectorizer.transform([user_query, metadata_text])
    
    cosine_sim = cosine_similarity(vectors[0], vectors[1])[0][0]
    return cosine_sim * 100

@functools.lru_cache(maxsize=1)
def get_all_points():
    """Retrieve all points from Qdrant and cache the results."""
    return qdrant_client.scroll(
        collection_name=QDRANT_COLLECTION_NAME,
        scroll_filter=None,
        with_vectors=False,
        with_payload=True,
        limit=200
    )[0]

def adjust_parameters_for_context(
    user_query: str,
    recent_history: Optional[List[Dict]] = None,
    config: RecommendationConfig = None,
    field_weights: Dict[str, float] = None
) -> Tuple[RecommendationConfig, Dict[str, float]]:
    """
    Dynamically adjust recommendation parameters based on user context.
    
    Args:
        user_query: The user's search query
        recent_history: User's recent browsing history
        config: Current recommendation config
        field_weights: Current field weights
        
    Returns:
        Tuple of (adjusted config, adjusted weights)
    """
    if config is None:
        config = RecommendationConfig()
    
    if field_weights is None:
        field_weights = FIELD_WEIGHTS.copy()
    else:
        field_weights = field_weights.copy()
    
    # Identify key terms in user query
    query_lower = user_query.lower()
    
    price_terms = ['cheap', 'budget', 'affordable', 'inexpensive', 'giá rẻ', 'rẻ', 'tiết kiệm']
    premium_terms = ['premium', 'high-end', 'luxury', 'best', 'cao cấp', 'xịn', 'đắt']
    
    if any(term in query_lower for term in price_terms):
        # For price-sensitive users
        field_weights['sale_price'] = field_weights.get('sale_price', 1.0) * 1.5
        field_weights['discount_percent'] = field_weights.get('discount_percent', 1.0) * 1.3
        config.MIN_MATCH_SCORE = config.MIN_MATCH_SCORE * 0.9  # Relax matching threshold
        
    elif any(term in query_lower for term in premium_terms):
        # For premium-focused users
        field_weights['sale_price'] = field_weights.get('sale_price', 1.0) * 0.7  # Reduce price importance
        for field in ['cpu', 'card', 'screen']:
            if field in field_weights:
                field_weights[field] = field_weights[field] * 1.3
    
    # Adjust for feature focus
    if 'gaming' in query_lower or 'game' in query_lower:
        field_weights['card'] = field_weights.get('card', 1.0) * 1.5  # Graphics card more important
        field_weights['cpu'] = field_weights.get('cpu', 1.0) * 1.3  # CPU more important
        
    if 'office' in query_lower or 'work' in query_lower or 'business' in query_lower:
        field_weights['suitable_for'] = field_weights.get('suitable_for', 1.0) * 1.5
    
    # Adjust for recent history - learn from past browsing
    if recent_history and len(recent_history) > 0:
        # If user has consistent brand history, boost that brand's importance
        brands = {}
        for item in recent_history:
            if 'device_name' in item:
                brand = item['device_name'].split()[0].lower() if item['device_name'] else ""
                if brand:
                    brands[brand] = brands.get(brand, 0) + 1
        
        # If more than 50% of history is same brand, boost its importance
        if brands and len(recent_history) > 0:
            max_brand, max_count = max(brands.items(), key=lambda x: x[1])
            if max_count / len(recent_history) > 0.5:
                # User has brand loyalty, boost brand importance
                field_weights['device_name'] = field_weights.get('device_name', 1.0) * 1.5
                config.HISTORY_BRAND_BOOST *= 1.5
    
    return config, field_weights

def recommend_system(
    user_input: str,
    types: Optional[str] = None,
    recent_history: Optional[List[Dict]] = None,
    preference: Optional[Dict[str, Any]] = None,
    custom_config: Optional[RecommendationConfig] = None,
    custom_weights: Optional[Dict[str, float]] = None,
    dynamic_adjustment: bool = True
) -> Tuple[str, Optional[List[str]]]:
    """
    Recommend products based on user input and preferences.
    
    Args:
        user_input: User's query text
        types: Product type filter
        recent_history: User's recent browsing history
        preference: User's preferences
        custom_config: Optional custom recommendation configuration
        custom_weights: Optional custom field weights
        dynamic_adjustment: Whether to dynamically adjust parameters based on context
        
    Returns:
        Tuple containing response text and list of retrieved device names
    """
    # Use custom config if provided, otherwise use default
    config = custom_config or RecommendationConfig()
    
    # Use custom weights if provided, otherwise use default
    field_weights = custom_weights or FIELD_WEIGHTS
    
    # Preprocess inputs
    user_query = f"{user_input.strip()} {types.strip() if types else ''}"
    language = detect(user_input)
    
    # Dynamically adjust parameters if enabled
    if dynamic_adjustment:
        config, field_weights = adjust_parameters_for_context(
            user_query, recent_history, config, field_weights
        )
    
    all_points = get_all_points()
    
    # Score calculation and filtering
    matched_docs = []
    user_query_lower = user_query.lower()
    
    for doc in all_points:
        metadata = doc.payload.get("metadata", {})
        
        # Base score calculation using config weights and custom field weights
        fuzzy_val = fuzzy_score(user_query_lower, metadata, field_weights)
        cosine_val = cosine_score(user_query_lower, metadata, field_weights)
        base_score = (config.FUZZY_WEIGHT * fuzzy_val + 
                      config.COSINE_WEIGHT * cosine_val)
        
        # History boost calculation
        history_boost = 0
        if recent_history:
            for past in recent_history:
                past_device = past.get("device_name", "")
                if past_device and past_device.split()[0] in metadata.get("device_name", ""):
                    history_boost += config.HISTORY_BRAND_BOOST
                if past.get("storage") == metadata.get("storage"):
                    history_boost += config.HISTORY_STORAGE_BOOST
                if past.get("colors") == metadata.get("colors"):
                    history_boost += config.HISTORY_COLOR_BOOST
        
        # Preference boost calculation
        preference_boost = 0
        if preference and "brand" in preference:
            device_name_lower = metadata.get("device_name", "").lower()
            for brand in preference["brand"]:
                brand_score = check_similarity(brand.lower(), device_name_lower)
                if brand_score > config.BRAND_SIMILARITY_THRESHOLD:
                    preference_boost += brand_score * config.BRAND_MATCH_BOOST
                    
            # Price range preference
            if "price_range" in preference:
                min_price, max_price = preference["price_range"]
                sale_price = metadata.get("sale_price")
                if isinstance(sale_price, (int, float)) and min_price <= sale_price <= max_price:
                    preference_boost += config.PRICE_RANGE_MATCH_BOOST

        # Calculate final score and filter
        final_score = base_score + history_boost + preference_boost
        if final_score > config.MIN_MATCH_SCORE:
            matched_docs.append({
                "doc": doc,
                "score": final_score
            })

    # Sort and slice for top results
    matched_docs.sort(key=lambda x: x["score"], reverse=True)
    context_docs = matched_docs[:config.MAX_RESULTS]

    # Handle no results case
    if not context_docs:
        return "I couldn't find any products matching your query. Could you try being more specific?", []

    # Build context and device list
    search_context = ""
    retrieved_devices = []
    
    # Key metadata fields to include in results
    meta_fields = [
        "cpu", "card", "screen", "storage",
        "sale_price", "original_price", "discount_percent", "installment_price",
        "colors", "sales_perks", "guarantee_program", "payment_perks", "source"
    ]
    
    for idx, item in enumerate(context_docs, start=1):
        meta = item["doc"].payload.get("metadata", {})
        device_name = meta.get("device_name", "Unknown Device")
        retrieved_devices.append(device_name)
        
        content = f"Product {idx}:\n"
        for field in meta_fields:
            if field in meta:
                if field in ["sale_price", "original_price", "installment_price"]:
                    content += f"- {field}: {meta[field]:,} VND\n"
                elif field == "discount_percent":
                    content += f"- {field}: {meta[field]}%\n"
                else:
                    content += f"- {field}: {meta[field]}\n"
        search_context += content + "\n\n"

    first_meta = context_docs[0]["doc"].payload.get("metadata", {})
    top_device_name = first_meta.get("device_name", "Unknown Device")

    llm = ai_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
                You are a helpful and friendly product assistant for FPT Shop, focus on selling phone and other technology devices.
                Your task is to recommend products based on the `search_context` and `user_query`.
                Instructions:
                - Reply in the same language {language} as the user's query.
                - Focus primarily on Product 1 with top_device_name: top_device_name, which has the highest match score for the user's query.
                - YOU MUST return information about , storage, sale_price, original_price, discount_percent, installment_price, colors, sales_perks, guarantee_program, payment_perks, source.
                - After highlighting the main recommendation, briefly mention other products as alternative options.
                - Use phrases like "Besides, we also have..." or "You may also be interested in..." when introducing other options.
                - List all products retrieved from search_context.
            """),
        ("human", "User query: {user_query}\n\nSearch results:\n{search_context}\n\nLanguage:\n{language}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "user_query": user_query_lower,
        "search_context": search_context,
        "language": language
    })
    
    return response.content if hasattr(response, 'content') else response, retrieved_devices

def get_device_details(user_query: str, device_name: str) -> str:
    """
    Retrieve detailed information about a specific device.
    
    Args:
        user_query: The original user query
        device_name: The device name to search for
        
    Returns:
        Detailed information about the device
    """
    
    language = detect(user_query)
    device_name_lower = device_name.lower()
    
    # Use cached query results
    all_points = get_all_points()
    
    # Find matching document
    matching_doc = None
    for doc in all_points:
        metadata = doc.payload.get("metadata", {})
        if metadata.get("device_name", "").lower() == device_name_lower:
            matching_doc = doc
            break
    
    if not matching_doc:
        return f"No detailed information found for {device_name}. Please try another product."
    
    detail = matching_doc.payload['page_content']
    llm = ai_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
                You are a helpful and friendly product assistant for FPT Shop, focus on selling phone and other technology devices.
                Your task is to provide detailed information about a specific device.
                MAKE SURE to return any founded links, images links as references.
                MAKE sure to return in the same detected language
            """),
        ("human", "device_name: {device_name}\n\nSearch results:\n{detail}\n\nLanguage:\n{language}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "device_name": device_name,
        "detail": detail,
        "language": language
    })
    
    return response.content