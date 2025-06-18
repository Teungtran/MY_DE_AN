from langchain_core.tools import tool
from rapidfuzz import fuzz
from langdetect import detect_langs
from pydantic import EmailStr
import numpy as np
from functools import lru_cache
from typing import List, Dict, Optional, Tuple
from schemas.device_schemas import RecommendationConfig, CancelOrder, Order, TrackOrder,RecommendSystem,UpdateOrder
from .get_score import (
    check_similarity, get_all_points, keyword, convert_to_string,
    batch_fuzzy_scoring, check_similarity_vectorized 
)
from config.base_config import APP_CONFIG
import time
import json
from .llm import llm_recommend, llm_device_detail
from sqlalchemy import text
from .get_sql import connect_to_db
from .get_id import generate_short_id
from utils.email import send_email
sql_config = APP_CONFIG.sql_config

db = connect_to_db(server="DESKTOP-LU731VP\\SQLEXPRESS", database="CUSTOMER_SERVICE")

recommended_devices_cache = []

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
            'combined_text': " ".join([
                convert_to_string(metadata.get("device_name", "")),
                convert_to_string(metadata.get("brand", "")),
                convert_to_string(metadata.get("category", "")),
                convert_to_string(metadata.get("sales_perks", "")),
                convert_to_string(metadata.get("sales_price", "")),
                convert_to_string(metadata.get("discount_percent", "")),
                convert_to_string(metadata.get("payment_perks", "")),
                convert_to_string(metadata.get("battery", "")),
                convert_to_string(metadata.get("cpu", "")),
                convert_to_string(metadata.get("card", "")),
                convert_to_string(metadata.get("storage", "")),
                convert_to_string(metadata.get("guarantee_program", "")),
            ]).lower()
        }
        processed_metadata.append(processed)
    
    _metadata_cache = processed_metadata
    _metadata_cache_timestamp = current_time
    return processed_metadata

def vectorized_scoring(
    processed_docs: List[Dict],
    main_query_lower: str,
    brands: List[str],
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
        fuzzy_scores = np.array(batch_fuzzy_scoring(main_query_lower, combined_texts))
    
    # Vectorized calculations
    scores = np.zeros(len(processed_docs))
    
    # User input scoring
    if main_query_lower:
        user_input_scores = (fuzzy_scores * recommendation_config.FUZZY_WEIGHT + 
                           cos_scores * 100 * recommendation_config.COSINE_WEIGHT)
        scores += user_input_scores
    
    # Brand matching (vectorized)
    if brands:
        brand_scores = np.array([
            sum(fuzz.partial_ratio(b, doc['brand']) for b in brands) / len(brands)
            if doc['brand'] else 0
            for doc in processed_docs
        ])
        scores += brand_scores * recommendation_config.BRAND_MATCH_BOOST / 100
    
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

@tool("recommendation_system", args_schema=RecommendSystem)
def recommend_system(
    user_input: str,
    user_id: str = None,
) -> Tuple[str, list[str]]: 
    """
    Optimized recommendation system with vectorized operations and intelligent caching.
    """
    recommendation_config = RecommendationConfig()
    query = text("SELECT preferences FROM Customer_info WHERE user_id = :user_id")
    with db._engine.connect() as conn:
        query_result = conn.execute(query, {"user_id": user_id}).fetchone()
    preference = json.loads(query_result[0]) if query_result else None
    main_query = ""
    main_query_lower = ""
    if user_input and user_input.strip():
        main_query = keyword(user_input)
        main_query_lower = main_query.lower()

    language = detect_language_cached(main_query_lower)

    brands = []
    price_min = price_max = None
    
    if preference:
        if preference.get("brand"):
            brands = [brand.lower() for brand in preference["brand"]]
        
        if preference.get("price_range"):
            price_range = preference["price_range"]
            if isinstance(price_range, list):
                if len(price_range) == 1:
                    price_max = float(price_range[0])
                elif len(price_range) >= 2:
                    price_min = float(price_range[0])
                    price_max = float(price_range[1])
    


    # Get pre-processed data
    all_points = get_all_points()
    processed_docs = preprocess_metadata_batch(all_points)
    
    if not processed_docs:
        return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

    # Vectorized scoring
    scored_results = vectorized_scoring(processed_docs=processed_docs,main_query_lower=main_query_lower,
                                        brands=brands,price_min=price_min,price_max=price_max,recommendation_config=RecommendationConfig)
    
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

    global recommended_devices_cache
    recommended_devices_cache = top_device_names
    
    return response.content if hasattr(response, 'content') else response, top_device_names


@tool("device_details")
def get_device_details(user_input: str, top_device_names: Optional[List[str]] = None, state: Optional[Dict] = None) -> str:
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
    quantity: str = "1",
    payment: str = "cash on delivery",
    shipping: bool = True,
    time: str = None,
    user_id: str = None,
    email: EmailStr = None
) -> dict:
    """
    Tool to order electronic product
    """
    try:
        order_id = f"ORDER_{generate_short_id()}"

        try:
            quantity_int = int(quantity)
        except ValueError:
            quantity_int = 1

        check_stock_query = text("SELECT in_store FROM Item WHERE device_name = :device_name")
        with db._engine.connect() as conn:
            result = conn.execute(check_stock_query, {"device_name": device_name}).fetchone()

            if not result:
                return {"error": f"Product '{device_name}' not found in inventory."}
            if result[0] < quantity_int:
                return {"error": f"Not enough stock for '{device_name}'."}

            # Insert order — price will be handled by trigger
            insert_query = text("""
                INSERT INTO [Order] (
                    order_id, device_name, address, customer_name, customer_phone,
                    quantity, payment, shipping, status, time_reservation, user_id
                ) VALUES (
                    :order_id, :device_name, :address, :customer_name, :customer_phone,
                    :quantity, :payment, :shipping, :status, :time_reservation, :user_id
                )
            """)
            conn.execute(insert_query, {
                "order_id": order_id,
                "device_name": device_name,
                "address": address,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "quantity": quantity_int,
                "payment": payment,
                "shipping": shipping,
                "status": "Processing",
                "time_reservation": time,
                "user_id": user_id
            })
            conn.commit()

            get_price_query = text("SELECT price FROM [Order] WHERE order_id = :order_id")
            order_price = conn.execute(get_price_query, {"order_id": order_id}).fetchone()[0]
            email_subject = "Your FPT Shop Order Confirmation & Temporary Password"
            email_body = f"""
                        Kính gửi {customer_name},

                        Cảm ơn bạn đã mua sắm tại FPT Shop!

                        Chúng tôi xin xác nhận đơn hàng {order_id} của bạn cho sản phẩm '{device_name}' đã được đặt thành công. Vui lòng xem lại thông tin đơn hàng dưới đây:

                        🛒 Thông tin đơn hàng
                        - Tên thiết bị: {device_name}
                        - Số lượng: {quantity_int}
                        - Phương thức vận chuyển: {shipping}
                        - Phương thức thanh toán: {payment}
                        - Địa chỉ giao hàng: {address}
                        - Số điện thoại: {customer_phone}
                        - Trạng thái đơn hàng: Đang xử lý
                        - Thời gian đặt hàng: {time}

                        💳 Số tiền cần thanh toán: {order_price}

                        Nếu bạn có bất kỳ câu hỏi hoặc thắc mắc nào, vui lòng liên hệ bộ phận chăm sóc khách hàng của chúng tôi qua:

                        Tư vấn mua hàng (Miễn phí)  
                        📞 1800.6601 (Nhánh 1)

                        Hỗ trợ kỹ thuật  
                        🛠️ 1800.6601 (Nhánh 2)

                        Góp ý, khiếu nại  
                        📢 1800.6616 (8:00 – 22:00)

                        Một lần nữa, xin cảm ơn bạn đã tin tưởng FPT Shop!

                        Trân trọng,  
                        Đội ngũ FPT Shop  
                        https://fptshop.com.vn
                        
                        ---------------------------ENGLISH VERSION BELOW ---------------------------
                        
                        Dear {customer_name},

                        Thank you for shopping with FPT Shop!

                        We’re pleased to confirm that your order {order_id} for the device '{device_name}' has been successfully placed. Please review the order details below:

                        🛒 Order Details
                        - Device Name: {device_name}
                        - Quantity: {quantity_int}
                        - Shipping Method: {shipping}
                        - Payment Method: {payment}
                        - Shipping Address: {address}
                        - Phone Number: {customer_phone}
                        - Order Status: Processing
                        - Reservation Time: {time}

                        💳 Amount Due: {order_price}

                        For any questions or concerns, please don't hesitate to contact our customer support team through:

                        Sales Consultation (Free of Charge)  
                        📞 1800.6601 (Press 1)

                        Technical Support  
                        🛠️ 1800.6601 (Press 2)

                        Feedback & Complaints  
                        📢 1800.6616 (8:00 AM – 10:00 PM)

                        Thank you again for choosing FPT Shop!

                        Best regards,  
                        FPT Shop Team  
                        https://fptshop.com.vn
            """

            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )

        return {
            "order_id": order_id,
            "device_name": device_name,
            "address": address,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "quantity": quantity_int,
            "payment": payment,
            "shipping": shipping,
            "status": "Processing",
            "time_reservation": time,
            "price": order_price,
            "message": f"Order {order_id} has been successfully placed for {device_name}.Please pay {order_price} for you order. For more information, please check your email."
        }

    except Exception as e:
        print(f"Error in order_purchase: {str(e)}")
        return {"error": f"Error placing order: {str(e)}"}
    
@tool("update_order", args_schema=UpdateOrder)
def update_order(
    order_id: str,
    device_name: Optional[str] = None,
    address:  Optional[str] = None,
    customer_name:  Optional[str] = None,
    customer_phone:  Optional[str] = None,
    quantity:  Optional[str] = None,
    payment:  Optional[str] = None,
    shipping: bool = None,
    time:  Optional[str] = None,
    user_id:  str = None,
    email: EmailStr = None

) -> dict:
    """
    Tool to update an existing order. Only `order_id` is required.
    Other fields will be updated if provided; otherwise, existing values are retained.
    """
    try:
        # check status
        with db._engine.connect() as conn:
            select_query = text("SELECT status FROM [Order] WHERE order_id = :order_id")
            status = conn.execute(select_query, {"order_id": order_id}).fetchone()
            if status[0] != "Processing":
                return {f"Order '{order_id}' has already been processed. You can't update it."}
        with db._engine.connect() as conn:
            select_query = text("SELECT * FROM [Order] WHERE order_id = :order_id")
            existing_order = conn.execute(select_query, {"order_id": order_id}).fetchone()

            if not existing_order:
                return {"error": f"Order '{order_id}' not found."}

            columns = existing_order._fields
            order_data = dict(zip(columns, existing_order))

            quantity_int = order_data["quantity"]
            if quantity:
                try:
                    quantity_int = int(quantity)
                except ValueError:
                    return {"error": "Quantity must be a valid number."}

                # Check stock if device_name is present or unchanged
                check_device = device_name or order_data["device_name"]
                stock_query = text("SELECT in_store FROM Item WHERE device_name = :device_name")
                stock_result = conn.execute(stock_query, {"device_name": check_device}).fetchone()
                if not stock_result:
                    return {"error": f"Device '{check_device}' not found in inventory."}
                if stock_result[0] < quantity_int:
                    return {"error": f"Not enough stock for '{check_device}'."}

            updated = {
                "device_name": device_name or order_data["device_name"],
                "address": address or order_data["address"],
                "customer_name": customer_name or order_data["customer_name"],
                "customer_phone": customer_phone or order_data["customer_phone"],
                "quantity": quantity_int,
                "payment": payment or order_data["payment"],
                "shipping": shipping if shipping is not None else order_data["shipping"],
                "time_reservation": time or order_data["time_reservation"],
                "order_id": order_id,
                "user_id": user_id
            }

            update_query = text("""
                UPDATE [Order]
                SET
                    device_name = :device_name,
                    address = :address,
                    customer_name = :customer_name,
                    customer_phone = :customer_phone,
                    quantity = :quantity,
                    payment = :payment,
                    shipping = :shipping,
                    time_reservation = :time_reservation
                WHERE order_id = :order_id
            """)
            conn.execute(update_query, updated)
            conn.commit()
            price_query = text("SELECT price FROM [Order] WHERE order_id = :order_id")
            order_price = conn.execute(price_query, {"order_id": order_id}).fetchone()[0]
            email_subject = "Your FPT Shop Order Has Been Updated"

            email_body = f"""\
            Dear {customer_name},

            Your order {order_id} has been successfully updated. Please review the latest order details below:

            🛒 Updated Order Details
            - Device Name: {device_name}
            - Quantity: {quantity}
            - Shipping Method: {shipping}
            - Payment Method: {payment}
            - Shipping Address: {address}
            - Phone Number: {customer_phone}
            - Reservation Time: {time}

            💳 Updated Total: {order_price}

            For any questions or concerns, please contact our customer support team:

            Sales Consultation (Free of Charge)  
            📞 1800.6601 (Press 1)

            Technical Support  
            🛠️ 1800.6601 (Press 2)

            Feedback & Complaints  
            📢 1800.6616 (8:00 AM – 10:00 PM)

            Thank you again for choosing FPT Shop!

            Best regards,  
            FPT Shop Team  
            https://fptshop.com.vn

            ---------------------------ENGLISH VERSION BELOW ---------------------------

            Kính gửi {customer_name},

            Đơn hàng {order_id} của bạn đã được cập nhật thành công. Vui lòng kiểm tra thông tin mới nhất bên dưới:

            🛒 Thông tin đơn hàng cập nhật
            - Tên thiết bị: {device_name}
            - Số lượng: {quantity}
            - Phương thức vận chuyển: {shipping}
            - Phương thức thanh toán: {payment}
            - Địa chỉ giao hàng: {address}
            - Số điện thoại: {customer_phone}
            - Thời gian đặt hàng: {time}

            💳 Tổng tiền sau cập nhật: {order_price}

            Mọi thắc mắc hoặc cần hỗ trợ, vui lòng liên hệ bộ phận chăm sóc khách hàng:

            Tư vấn mua hàng (Miễn phí)  
            📞 1800.6601 (Nhánh 1)

            Hỗ trợ kỹ thuật  
            🛠️ 1800.6601 (Nhánh 2)

            Góp ý, khiếu nại  
            📢 1800.6616 (8:00 – 22:00)

            Cảm ơn bạn đã tin tưởng lựa chọn FPT Shop!

            Trân trọng,  
            Đội ngũ FPT Shop  
            https://fptshop.com.vn
            """
        if email:
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )
        return {
            "order_id": order_id,
            "device_name": updated["device_name"],
            "address": updated["address"],
            "customer_name": updated["customer_name"],
            "customer_phone": updated["customer_phone"],
            "quantity": updated["quantity"],
            "payment": updated["payment"],
            "shipping": updated["shipping"],
            "time_reservation": updated["time_reservation"],
            "price": order_price,
            "message": f"Order {order_id} has been successfully updated. For more information please check your email."
        }

    except Exception as e:
        print(f"Error in update_order: {str(e)}")
        return {"error": f"Error updating order: {str(e)}"}
@tool("cancel_order",args_schema=CancelOrder)
def cancel_order(
    order_id: str,
    email: EmailStr = None
) -> str:
    """
    Tool to cancel order by order id
    """
    try:
        check_query = text("SELECT status FROM [Order] WHERE order_id = :order_id")
        with db._engine.connect() as conn:
            result = conn.execute(check_query, {"order_id": order_id}).fetchone()

        if not result:
            return f"Order with ID {order_id} not found."

        if result[0] in ["Shipped", "Received", "Canceled", "Returned"]:
            return f"Cannot cancel order. Current status: {result[0]}"

        update_query = text("UPDATE [Order] SET status = 'Canceled' WHERE order_id = :order_id")
        with db._engine.connect() as conn:
            conn.execute(update_query, {"order_id": order_id})
            conn.commit()
        email_subject = "Your FPT Shop Order Has Been Canceled"

        email_body = f"""
                Kính gửi Quý khách,

                Đơn hàng của bạn với mã số {order_id} đã được hủy thành công.

                Nếu bạn không yêu cầu hủy hoặc muốn đặt lại đơn hàng, vui lòng truy cập website của chúng tôi hoặc liên hệ tổng đài hỗ trợ.

                📞 Tư vấn mua hàng (Miễn phí): 1800.6601 (Nhánh 1)  
                🛠 Hỗ trợ kỹ thuật: 1800.6601 (Nhánh 2)  
                📢 Góp ý, khiếu nại: 1800.6616 (8:00 – 22:00)

                Cảm ơn bạn đã tin tưởng FPT Shop!

                Trân trọng,  
                Đội ngũ FPT Shop  
                https://fptshop.com.vn
            ---------------------------ENGLISH VERSION BELOW ---------------------------

                Dear Customer,

                Your order with order ID {order_id} has been successfully cancelled.

                If you do not require cancellation or want to place another order, please visit our website or contact our customer support.

                📞 Customer Support (Free Call): 1800.6601 (Call Center 1)
                """
        if email:
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )
        return f"Order {order_id} cancelled successfully."

    except Exception as e:
        return f"Error cancelling order: {str(e)}"

@tool("track_order",args_schema=TrackOrder)
def track_order(order_id: str) -> list[dict]:
    """
    Tool to track order info and status by order id
    """
    try:
        track_query = text("""
            SELECT *
            FROM [Order]
            WHERE order_id = :order_id
        """)
        with db._engine.connect() as conn:
            result = conn.execute(track_query, {"order_id": order_id}).fetchone()

        if not result:
            return f"Order with ID {order_id} not found."
        return result


    except Exception as e:
        return f"Error tracking order: {str(e)}"

