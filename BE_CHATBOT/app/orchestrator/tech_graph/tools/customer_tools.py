from langchain_core.tools import tool
from rapidfuzz import fuzz
from langdetect import detect_langs
import numpy as np
from functools import lru_cache
from typing import List, Dict, Optional, Any, Tuple
from schemas.device_schemas import RecommendationConfig, CancelOrder, Order, TrackOrder,BookAppointment
from .get_score import (
    check_similarity, get_all_points, keyword, convert_to_string,
    batch_fuzzy_scoring, check_similarity_vectorized 
)
import time
from .llm import llm_recommend, llm_device_detail

# Global cache for recommended devices
recommended_devices_cache = []

# Cache for processed metadata to avoid repeated extraction
_metadata_cache = {}
_metadata_cache_timestamp = 0
METADATA_CACHE_DURATION = 300  # 5 minutes

@lru_cache(maxsize=100)
def detect_language_cached(text: str) -> str:
    """Cached language detection to avoid repeated calls."""
    try:
        return detect_langs(text)[0].lang if text else 'en'
    except:
        return 'en'

def preprocess_metadata_batch(all_points: List) -> List[Dict]:
    """Pre-process all metadata once for efficient filtering."""
    global _metadata_cache, _metadata_cache_timestamp
    
    current_time = time.time()
    if (_metadata_cache and 
        current_time - _metadata_cache_timestamp < METADATA_CACHE_DURATION):
        return _metadata_cache
    
    processed_metadata = []
    for doc in all_points:
        metadata = doc.payload.get("metadata", {})
        
        # Pre-process commonly used fields
        processed = {
            'doc': doc,
            'device_name': convert_to_string(metadata.get("device_name", "")).lower(),
            'brand': convert_to_string(metadata.get("brand", "")).lower(),
            'category': convert_to_string(metadata.get("category", "")).lower(),
            'suitable_for': convert_to_string(metadata.get("suitable_for", "")).lower(),
            'sale_price': metadata.get("sale_price"),
            'combined_text': " ".join([
                convert_to_string(metadata.get("device_name", "")),
                convert_to_string(metadata.get("brand", "")),
                convert_to_string(metadata.get("category", "")),
                convert_to_string(metadata.get("sales_perks", "")),
                convert_to_string(metadata.get("sales_price", "")),
                convert_to_string(metadata.get("discount_percent", "")),
                convert_to_string(metadata.get("payment_perks", ""))
            ]).lower(),
            'raw_metadata': metadata  # Keep original for final output
        }
        processed_metadata.append(processed)
    
    _metadata_cache = processed_metadata
    _metadata_cache_timestamp = current_time
    return processed_metadata

def vectorized_scoring(
    processed_docs: List[Dict],
    main_query_lower: str,
    user_types: List[str],
    brands: List[str],
    history_device_names: List[str],
    price_min: Optional[float],
    price_max: Optional[float],
    recommendation_config: RecommendationConfig
) -> List[Tuple[Dict, float]]:
    """Vectorized scoring for all documents at once."""
    
    if not processed_docs:
        return []
    
    combined_texts = [doc['combined_text'] for doc in processed_docs]
    
    # Batch cosine similarity calculation
    cos_scores = np.array([0.0] * len(processed_docs))
    if main_query_lower:
        # Use vectorized similarity if available, fallback to individual
        try:
            cos_scores = check_similarity_vectorized(main_query_lower)
            if len(cos_scores) != len(processed_docs):
                cos_scores = np.array([
                    check_similarity(main_query_lower, [text]) 
                    for text in combined_texts
                ])
        except:
            cos_scores = np.array([
                check_similarity(main_query_lower, [text]) 
                for text in combined_texts
            ])
    
    # Batch fuzzy scoring
    fuzzy_scores = np.array([0.0] * len(processed_docs))
    if main_query_lower:
        raw_metadatas = [doc['raw_metadata'] for doc in processed_docs]
        fuzzy_scores = np.array(batch_fuzzy_scoring(main_query_lower, raw_metadatas))
    
    # Vectorized calculations
    scores = np.zeros(len(processed_docs))
    
    # User input scoring
    if main_query_lower:
        user_input_scores = (fuzzy_scores * recommendation_config.FUZZY_WEIGHT + 
                           cos_scores * 100 * recommendation_config.COSINE_WEIGHT)
        scores += user_input_scores
    
    # Type matching (vectorized)
    if user_types:
        type_scores = np.array([
            sum(fuzz.partial_ratio(t, doc['suitable_for']) for t in user_types) / len(user_types)
            if doc['suitable_for'] else 0
            for doc in processed_docs
        ])
        scores += type_scores * recommendation_config.TYPE_MATCH_BOOST / 100
    
    # Brand matching (vectorized)
    if brands:
        brand_scores = np.array([
            sum(fuzz.partial_ratio(b, doc['brand']) for b in brands) / len(brands)
            if doc['brand'] else 0
            for doc in processed_docs
        ])
        scores += brand_scores * recommendation_config.BRAND_MATCH_BOOST / 100
    
    # Price filtering (vectorized)
    if price_min is not None or price_max is not None:
        price_scores = np.zeros(len(processed_docs))
        for i, doc in enumerate(processed_docs):
            sale_price = doc['sale_price']
            if isinstance(sale_price, (int, float)):
                if (price_min is not None and price_max is not None and 
                    price_min <= sale_price <= price_max):
                    price_scores[i] = recommendation_config.PRICE_RANGE_MATCH_BOOST
                elif price_max is not None and sale_price <= price_max:
                    price_scores[i] = recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
                elif price_min is not None and sale_price >= price_min:
                    price_scores[i] = recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
        scores += price_scores
    
    # History matching (vectorized)
    if history_device_names:
        history_scores = np.array([
            sum(fuzz.partial_ratio(h, f"{doc['category']} {doc['brand']} {doc['device_name']}") 
                for h in history_device_names) / len(history_device_names)
            for doc in processed_docs
        ])
        scores += history_scores * recommendation_config.HISTORY_MATCH_BOOST / 100
    
    # Create results with early filtering
    results = []
    threshold = 50 if main_query_lower else 0
    
    for i, (doc, score) in enumerate(zip(processed_docs, scores)):
        if score >= threshold:
            results.append((doc, score))
    
    return results

@lru_cache(maxsize=50)
def build_search_context_cached(device_names_tuple: Tuple[str, ...], top_matches_data: str) -> str:
    """Cached search context building for repeated queries."""
    return _build_search_context(device_names_tuple, top_matches_data)

def _build_search_context(device_names_tuple: Tuple[str, ...], top_matches_data: str) -> str:
    """Internal function to build search context."""
    # This would contain the actual context building logic
    # For caching purposes, we need to serialize the top_matches_data
    return top_matches_data

def build_search_context_optimized(top_matches: List[Tuple[Dict, float]]) -> str:
    """Optimized search context building with pre-computed strings."""
    meta_fields = [
        "device_name", "cpu", "card", "screen", "storage", "image_link",
        "sale_price", "discount_percent", "installment_price",
        "colors", "sales_perks", "guarantee_program", "payment_perks", "source"
    ]
    
    # Pre-allocate list for better memory performance
    search_context_parts = []
    
    for idx, (processed_doc, score) in enumerate(top_matches, start=1):
        meta = processed_doc['raw_metadata']
        content_parts = [f"Product {idx}:"]
        
        # Process fields in batch to reduce function call overhead
        for field in meta_fields:
            if field in meta and meta[field]:  # Skip empty values
                value = meta[field]
                if field in ["sale_price", "installment_price"]:
                    if isinstance(value, (int, float)):
                        content_parts.append(f"- {field}: {value:,} VND")
                    else:
                        content_parts.append(f"- {field}: {value} VND")
                elif field == "discount_percent":
                    content_parts.append(f"- {field}: {value}%")
                else:
                    content_parts.append(f"- {field}: {value}")
        
        search_context_parts.append("\n".join(content_parts))
    
    return "\n\n".join(search_context_parts)

@tool("recommendation_system")
def recommend_system(
    user_input: str,
    types: Optional[str] = None,
    recent_history: Optional[List[Dict]] = None,
    preference: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None  
) -> Tuple[str, list[str]]: 
    """
    Optimized recommendation system with vectorized operations and intelligent caching.
    """
    recommendation_config = RecommendationConfig()
    
    # Pre-process inputs once with early validation
    main_query = ""
    main_query_lower = ""
    if user_input and user_input.strip():
        main_query = keyword(user_input)
        main_query_lower = main_query.lower()
    
    # Cached language detection
    language_input = user_input or types or ""
    if not language_input and preference and preference.get("brand"):
        language_input = preference["brand"][0]
    language = detect_language_cached(language_input)

    # Pre-process preference filters with default values
    brands = []
    user_types = []
    history_device_names = []
    price_min = price_max = None
    
    if preference:
        if preference.get("brand"):
            brands = [brand.lower() for brand in preference["brand"]]
        
        if preference.get("price_range"):
            price_range = preference["price_range"]
            if isinstance(price_range, list):
                if len(price_range) == 1:
                    price_max = price_range[0]
                elif len(price_range) >= 2:
                    price_min, price_max = price_range[:2]
    
    if types:
        user_types = types.lower().split()
    
    if recent_history:
        history_device_names = [
            rh["device_name"].lower() for rh in recent_history 
            if isinstance(rh, dict) and rh.get("device_name")
        ]

    # Get pre-processed data
    all_points = get_all_points()
    processed_docs = preprocess_metadata_batch(all_points)
    
    if not processed_docs:
        return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

    # Vectorized scoring
    scored_results = vectorized_scoring(
        processed_docs, main_query_lower, user_types, brands,
        history_device_names, price_min, price_max, recommendation_config
    )
    
    if not scored_results:
        return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

    # Sort and limit results
    scored_results.sort(key=lambda x: x[1], reverse=True)
    top_match_count = min(len(scored_results), recommendation_config.MAX_RESULTS)
    top_matches = scored_results[:top_match_count]
    
    # Extract device names efficiently
    top_device_names = [
        match[0]['raw_metadata'].get("device_name") 
        for match in top_matches 
        if match[0]['raw_metadata'].get("device_name")
    ]

    # Build search context
    search_context = build_search_context_optimized(top_matches)
    
    # Get source and images from first match
    first_meta = top_matches[0][0]['raw_metadata'] if top_matches else {}
    source = first_meta.get("source", "")
    images = first_meta.get("image_link", "")

    # Generate response
    response = llm_recommend(user_input, search_context, language, top_device_names, source, images)

    # Update global cache
    global recommended_devices_cache
    recommended_devices_cache = top_device_names
    
    return response.content if hasattr(response, 'content') else response, top_device_names


@tool("device_details")
def get_device_details(user_input: str, top_device_names: Optional[List[str]] = None, state: Optional[Dict] = None,conversation_id: Optional[str] = None) -> str:
    """
    Retrieve detailed information about a specific device.
    Uses a cache to avoid repeated lookups for the same device.

    Args:
        user_input: User query text for selecting a device
        top_device_names: List of recommended device names (optional)
        state: Current state containing recommended devices (optional)
    """
    try:
        language = detect_langs(user_input)
        
        # Try to get device names from various sources in order of priority
        device_names = None
        
        # 1. Directly provided top_device_names parameter
        if top_device_names and isinstance(top_device_names, list) and len(top_device_names) > 0:
            device_names = top_device_names
            print(f"Using provided top_device_names with {len(device_names)} devices")
        
        # 2. State's recommended_devices
        elif state and isinstance(state, dict) and "recommended_devices" in state:
            state_devices = state["recommended_devices"]
            if isinstance(state_devices, list) and len(state_devices) > 0:
                device_names = state_devices
                print(f"Using state.recommended_devices with {len(device_names)} devices")
        
        # 3. Global cache
        elif recommended_devices_cache and len(recommended_devices_cache) > 0:
            device_names = recommended_devices_cache
            print(f"Using global recommended_devices_cache with {len(device_names)} devices")
        
        if not device_names or len(device_names) == 0:
            return "No recommended devices available. Please search for devices first."

        scored_devices = [
            (rec_device, fuzz.ratio(user_input.lower(), rec_device.lower()))
            for rec_device in device_names
        ]

        top_device, top_score = max(scored_devices, key=lambda x: x[1])
        print(f"Top matched device: {top_device} (score: {top_score})")

        all_points = get_all_points()
        matching_doc = next(
            (doc for doc in all_points
            if doc.payload.get("metadata", {}).get("device_name", "").lower() == top_device.lower()),
            None
        )

        if not matching_doc:
            return f"No detailed information found for '{top_device}'. Please try another product."

        # Extract detail and metadata
        detail = matching_doc.payload['page_content']
        metadata = matching_doc.payload.get("metadata", {})
        device_name = metadata.get("device_name", top_device)
        source = metadata.get("source", "FPT Shop")

        response = llm_device_detail(language, detail, source, device_name)
        return response
    except Exception as e:
        return f"An error occurred: {str(e)}"



@tool("order_purchase",args_schema=Order)
def order_purchase(
    device_name: str,
    address: str,
    customer_name: str = None,
    customer_phone: str = None,
    time: str = None,
    quantity: str = None,
    payment: str = "cash on delivery",
    shipping: bool = "shipping",
    conversation_id: Optional[str] = None
) -> str:
    """
    Tool to order electronic product
    """
    
    
    
    return "Order successfully."


@tool("cancel_order",args_schema=CancelOrder)
def cancel_order(
    order_id: str,
    conversation_id: Optional[str] = None
) -> str:
    """
    Tool to cancel order by order id
    """
    return "Cancel successfully."
@tool("track_order",args_schema=TrackOrder)
def track_order(
    order_id: str
) -> str:
    """
    Tool to track order info and status by order id
    """
    return "tracking order, your order is being process"

@tool("book_appointment", args_schema=BookAppointment)
def book_appointment(
    reason: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    time: str = None, 
    note: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> str:
    """
    Tool to book an appointment for the customer.
    """

    return f"Appointment booked for {customer_name or 'Customer'} on {time} for reason: {reason}."
