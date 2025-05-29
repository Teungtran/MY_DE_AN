from langchain_core.tools import tool
from rapidfuzz import fuzz
from langdetect import detect_langs

from typing import List, Dict, Optional, Any, Tuple
from schemas.device_schemas import RecommendationConfig, CancelOrder, Order, TrackOrder
from .get_score import fuzzy_score, check_similarity,get_all_points,keyword,convert_to_string
from.llm import llm_recommend, llm_device_detail
# Global cache for recommended devices
recommended_devices_cache = []

@tool("recommendation_system")
def recommend_system(
    user_input: str,
    types: Optional[str] = None,
    recent_history: Optional[List[Dict]] = None,
    preference: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None  
) -> Tuple[str, list[str]]: 
    """
    Recommend products based on user input, types, preferences, and history.
    User input is optional - system can recommend based on other parameters if not provided.
    
    Args:
        state: Current state containing messages and recommended devices
        types: Type of device to search for
        recent_history: History of user's previous interactions
        preference: User preferences for filtering results
        custom_config: Custom configuration for recommendation engine
        global_config: Global config that may contain recommended devices for persistence
    """
    recommendation_config = RecommendationConfig()
    
    # Pre-process inputs once
    main_query = ""
    main_query_lower = ""
    if user_input:
        main_query = keyword(user_input)
        main_query_lower = main_query.lower()
    
    # Determine language once
    language_input = user_input or types or ""
    if not language_input and preference and "brand" in preference and preference["brand"]:
        language_input = preference["brand"][0]
    language = detect_langs(language_input)

    # Pre-process preference filters
    brands = []
    user_types = []
    history_device_names = []
    price_min = price_max = None
    
    if preference and "brand" in preference and preference["brand"]:
        brands = [brand.lower() for brand in preference["brand"]]
    
    if types:
        user_types = types.lower().split()
    
    if recent_history:
        history_device_names = [rh["device_name"].lower() for rh in recent_history 
                            if isinstance(rh, dict) and "device_name" in rh]
    
    if preference and "price_range" in preference and preference["price_range"]:
        price_range = preference["price_range"]
        if isinstance(price_range, list):
            if len(price_range) == 1:
                price_max = price_range[0]
            elif len(price_range) >= 2:
                price_min, price_max = price_range[:2]

    # Use flags to check if filters exist
    has_brands = len(brands) > 0
    has_types = len(user_types) > 0
    has_history = len(history_device_names) > 0
    has_price = price_min is not None or price_max is not None

    all_points = get_all_points()
    matched_docs = []

    for doc in all_points:
        metadata = doc.payload.get("metadata", {})
        total_score = 0
        
        # User input scoring (most expensive operation first to potentially skip)
        if user_input:
            combined_fields = [
                convert_to_string(metadata.get("device_name", "")),
                convert_to_string(metadata.get("brand", "")),
                convert_to_string(metadata.get("category", "")),
                convert_to_string(metadata.get("sales_perks", "")),
                convert_to_string(metadata.get("sales_price", "")),
                convert_to_string(metadata.get("discount_percent", "")),
                convert_to_string(metadata.get("payment_perks", ""))
            ]
            cos_score = check_similarity(main_query_lower, combined_fields)
            user_input_score = fuzzy_score(main_query_lower, metadata)
            total_score += user_input_score * recommendation_config.FUZZY_WEIGHT + cos_score * 100 * recommendation_config.COSINE_WEIGHT
        
        # Early filtering - skip if score is too low and we have user input
        if user_input and total_score < 50:  # Threshold to skip low-scoring items early
            continue
        
        # Type matching
        if has_types:
            doc_category = metadata.get("suitable_for", "").lower()
            if doc_category:
                type_score = sum(fuzz.partial_ratio(t, doc_category) for t in user_types)
                total_score += (type_score / len(user_types)) * recommendation_config.TYPE_MATCH_BOOST / 100
        
        # Brand matching
        if has_brands:
            doc_brand = metadata.get("brand", "").lower()
            if doc_brand:
                brand_score = sum(fuzz.partial_ratio(b, doc_brand) for b in brands)
                total_score += (brand_score / len(brands)) * recommendation_config.BRAND_MATCH_BOOST / 100
        
        # Price filtering
        if has_price:
            sale_price = metadata.get("sale_price")
            if isinstance(sale_price, (int, float)):
                if price_min is not None and price_max is not None and price_min <= sale_price <= price_max:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST
                elif price_max is not None and sale_price <= price_max:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
                elif price_min is not None and sale_price >= price_min:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
        
        # History matching
        if has_history:
            doc_info = f"{metadata.get('category', '').lower()} {metadata.get('brand', '').lower()} {metadata.get('device_name', '').lower()}"
            history_score = sum(fuzz.partial_ratio(h, doc_info) for h in history_device_names)
            total_score += (history_score / len(history_device_names)) * recommendation_config.HISTORY_MATCH_BOOST / 100
        
        matched_docs.append({
            "doc": doc,
            "score": total_score
        })

    # Sort and get top matches
    matched_docs.sort(key=lambda x: x["score"], reverse=True)
    top_match_count = min(len(matched_docs), recommendation_config.MAX_RESULTS)
    top_matches = matched_docs[:top_match_count]
    
    # Extract device names once
    top_device_names = [match["doc"].payload.get("metadata", {}).get("device_name") 
                       for match in top_matches if match["doc"].payload.get("metadata", {}).get("device_name")]

    if not top_matches:
        return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

    # Build search context efficiently
    meta_fields = [
        "device_name", "cpu", "card", "screen", "storage", "image_link",
        "sale_price", "discount_percent", "installment_price",
        "colors", "sales_perks", "guarantee_program", "payment_perks", "source"
    ]

    search_context_parts = []
    for idx, item in enumerate(top_matches, start=1):
        meta = item["doc"].payload.get("metadata", {})
        content_parts = [f"Product {idx}:"]
        
        for field in meta_fields:
            if field in meta:
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
    
    search_context = "\n\n".join(search_context_parts)
    
    # Get source and images from first match
    first_meta = top_matches[0]["doc"].payload.get("metadata", {}) if top_matches else {}
    source = first_meta.get("source", "")
    images = first_meta.get("image_link", "")

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