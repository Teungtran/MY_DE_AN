from langchain_core.tools import tool
from rapidfuzz import process
from rapidfuzz.fuzz import partial_ratio,token_sort_ratio 
from collections import defaultdict
from pydantic import EmailStr
from typing import List, Dict, Optional, Tuple
from schemas.device_schemas import RecommendationConfig, CancelOrder, Order, TrackOrder, RecommendSystem, UpdateOrder
from .get_score import (
    check_similarity, get_all_points, convert_to_string)
from config.base_config import APP_CONFIG
import json
from .get_id import generate_short_id
from utils.email import send_email
from models.database import CustomerInfo, Order as OrderModel, Item, SessionLocal
import heapq
sql_config = APP_CONFIG.sql_config

# Create a function to get a database session
def get_shop_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

recommended_devices_cache = []
METADATA_CACHE_DURATION = 300  
def get_other_preference(user_id):
    db = get_shop_db()
    try:
        user = db.query(CustomerInfo).filter(CustomerInfo.user_id == user_id).first()
        if not user or user.age is None:
            return {}
        
        similar_users = db.query(CustomerInfo.preferences).filter(
            CustomerInfo.age.between(user.age - 3, user.age + 3),
            CustomerInfo.preferences.isnot(None)
        ).all()
        
        merged_preferences = {}
        all_prefs = [json.loads(row[0]) for row in similar_users if row[0]]

        for pref in all_prefs:
            for key, val in pref.items():
                if isinstance(val, list):
                    merged_preferences.setdefault(key, set()).update(val)
                else:
                    merged_preferences[key] = val 

        for key in merged_preferences:
            if isinstance(merged_preferences[key], set):
                merged_preferences[key] = list(merged_preferences[key])
                
        return merged_preferences
        
    finally:
        db.close()


@tool("recommendation_system", args_schema=RecommendSystem)
def recommend_system(
    user_input: str,
    type :str = None,
    user_id: str = None,
    price: str = None
) -> Tuple[str, list[str]]: 
    """
    Recommend products based on user input, type , preferences, and history.
    User input is optional - system can recommend based on other parameters if not provided.
    
    Args:
        state: Current state containing messages and recommended devices
        type : Type of device to search for
        recent_history: History of user's previous interactions
        preference: User preferences for filtering results
        custom_config: Custom configuration for recommendation engine
        global_config: Global config that may contain recommended devices for persistence
    """
    recommendation_config = RecommendationConfig()
    db = get_shop_db()
    
    try:
        user = db.query(CustomerInfo).filter(CustomerInfo.user_id == user_id).first()
        preference = json.loads(user.preferences) if user and user.preferences else None
    finally:
        db.close()
    main_query_lower = ""
    if user_input:
        main_query_lower = user_input.lower()

    all_points = get_all_points(type=type)
    matched_docs = []
    has_brands = has_price = has_price_input = False
    brands = []
    merged_pref = defaultdict(set)
    age_pref = get_other_preference(user_id)
    for source in [preference, age_pref]:
        for k, v in source.items():
            if isinstance(v, list):
                merged_pref[k].update(map(str.lower, v))
            else:
                merged_pref[k].add(str(v).lower())

    preference = {k: list(v) for k, v in merged_pref.items()}

    for k, v in preference.items():
        if not isinstance(v, list):
            preference[k] = [v]
        else:
            preference[k] = list(set(v))
    
    if preference and "brand" in preference and preference["brand"]:
        all_brands = []
        for brand_entry in preference["brand"]:
            if ',' in str(brand_entry):
                split_brands = [b.strip().lower() for b in str(brand_entry).split(',')]
                all_brands.extend(split_brands)
            else:
                all_brands.append(str(brand_entry).lower())
        
        brands = list(set(all_brands))  
        has_brands = len(brands) > 0
    
    price_input = []
    if price:
        price_input = [price]
        has_price_input = True
    
    price_min = price_max = None
    price_range = preference.get("price_range", []) if preference else []
    if price_range:
        has_price = True
        numeric_prices = []
        for p in price_range:
            try:
                numeric_prices.append(float(p))
            except (ValueError, TypeError):
                continue
        
        if numeric_prices:
            price_min = min(numeric_prices)
            price_max = max(numeric_prices)

    for doc in all_points:
        meta = doc.payload.get("metadata", {})
        
        if not meta.get("brand") or meta.get("sale_price") is None:
            continue

        sale_price = meta.get("sale_price")
        
        if price_max and isinstance(sale_price, (int, float)):
            if sale_price > price_max * 1.2:  # Allow 20% over max
                continue

        total_score = 0

        text_fields = [
            "device_name", "brand", "discount_percent", "sales_price", "battery", "cpu", "card",
            "storage", "guarantee_program","sales_perks", "payment_perks"
        ]
        if len(main_query_lower.split()) < 5:
            function = partial_ratio
        else:
            function = token_sort_ratio
            
        combined_text = " ".join([convert_to_string(meta.get(field, "")) for field in text_fields])
        meta["combined_text"] = combined_text
        matches = process.extract(
            query=main_query_lower,
            choices=meta["combined_text"],
            scorer=function,
            limit=None
        )
        best_matches = [match for match in matches if match[1] > 60]

        if best_matches:
            fuzzy_score_val = max(best_matches, key=lambda x: x[1])[1]
        else:
            fuzzy_score_val = 0
        if fuzzy_score_val < 95:
            cos_score = check_similarity(main_query_lower, [combined_text])
        else:
            cos_score = 0
        total_score += fuzzy_score_val * recommendation_config.FUZZY_WEIGHT + cos_score * 100 * recommendation_config.COSINE_WEIGHT

        if has_brands:
            doc_brand = meta.get("brand", "").lower()
            best_match = process.extractOne(doc_brand, brands, scorer=partial_ratio)
            best_brand_score = best_match[1] if best_match else 0

            if best_brand_score >= 90:
                total_score += recommendation_config.BRAND_MATCH_STRONG
            elif best_brand_score >= 75:
                total_score += recommendation_config.BRAND_MATCH_MEDIUM
            elif best_brand_score >= 50:
                total_score += recommendation_config.BRAND_MATCH_WEAK
            else:
                total_score += recommendation_config.BRAND_MISMATCH_PENALTY
                
        if has_price_input:
            try:
                price_number = float(price_input[0])
                price_diff = abs(sale_price - price_number) / price_number
                price_similarity = max(0, 1 - price_diff)
                total_score += price_similarity * recommendation_config.PRICE_RANGE_MATCH_BOOST
            except:
                pass
            
        elif has_price:
            if isinstance(sale_price, (int, float)):
                if price_min is not None and price_max is not None and price_min <= sale_price <= price_max:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST
                elif price_max is not None and sale_price <= price_max:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
                elif price_min is not None and sale_price >= price_min:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7


        matched_docs.append({
            "doc": doc,
            "score": total_score
        })


    top_match_count = recommendation_config.get_max_results(type)
    top_matches = heapq.nlargest(top_match_count, matched_docs, key=lambda x: x["score"])
    
    top_device_names = []
    for match in top_matches:
        device_name = match["doc"].payload.get("metadata", {}).get("device_name")
        if device_name:
            top_device_names.append(device_name)

    if not top_matches:
        return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

    meta_fields = [
        "device_name", "cpu", "card", "screen", "storage", "image_link",
        "sale_price", "discount_percent", "installment_price", "sales_perks", 
        "guarantee_program", "payment_perks", "source"
    ]

    products_info = []
    for idx, item in enumerate(top_matches, start=1):
        meta = item["doc"].payload.get("metadata", {})
        content = f"Product {idx}:\n"
        for field in meta_fields:
            if field in meta and meta[field]:  
                if field in ["sale_price", "installment_price"]:
                    value = meta[field]
                    if isinstance(value, (int, float)):
                        content += f"- {field}: {value:,} VND\n"
                    else:
                        content += f"- {field}: {value} VND\n"
                elif field == "discount_percent":
                    content += f"- {field}: {meta[field]}%\n"
                else:
                    content += f"- {field}: {meta[field]}\n"
        products_info.append(content)
    
    search_context = "\n\n".join(products_info)

    global recommended_devices_cache
    recommended_devices_cache = top_device_names
    
    return search_context, top_device_names



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
            (rec_device, partial_ratio(user_input.lower(), rec_device.lower()))
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

        detail = matching_doc.payload.get('page_content', '')
        price = str(matching_doc.payload['metadata'].get('price', 'N/A'))
        sale_perks = matching_doc.payload['metadata'].get('sales_perks', '')

        if isinstance(sale_perks, list):
            sale_perks = ", ".join(map(str, sale_perks))
        else:
            sale_perks = str(sale_perks)

        content = f"{detail}\n\nSales Perks: {sale_perks}\nPrice: {price} VND"
        return content
    except Exception as e:
        return f"An error occurred: {str(e)}"

@tool("order_purchase", args_schema=Order)
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

        # Get a database session
        db = get_shop_db()
        
        try:
            # Check if the item exists and has enough stock
            item = db.query(Item).filter(Item.device_name == device_name).first()
            
            if not item:
                return {"error": f"Product '{device_name}' not found in inventory."}
                
            if item.in_store < quantity_int:
                return {"error": f"Not enough stock for '{device_name}'."}
                
            # Create a new order
            new_order = OrderModel(
                order_id=order_id,
                device_name=device_name,
                address=address,
                customer_name=customer_name,
                customer_phone=customer_phone,
                quantity=quantity_int,
                payment=payment,
                shipping=shipping,
                status="Processing",
                time_reservation=time,
                user_id=user_id,
                price=item.price * quantity_int  # Calculate price based on item price and quantity
            )
            
            # Add the order to the database
            db.add(new_order)
            db.commit()
            
            # Get the order price for the response
            order_price = new_order.price
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

        # Send email confirmation
        if email:
            email_subject = "Your FPT Shop Order Confirmation"
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
                        - Thời gian nhận hàng: {time}

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

                        We're pleased to confirm that your order {order_id} for the device '{device_name}' has been successfully placed. Please review the order details below:

                        🛒 Order Details
                        - Device Name: {device_name}
                        - Quantity: {quantity_int}
                        - Shipping Method: {shipping}
                        - Payment Method: {payment}
                        - Shipping Address: {address}
                        - Phone Number: {customer_phone}
                        - Order Status: Processing
                        - Shipping Time: {time}

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
    address: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    quantity: Optional[str] = None,
    payment: Optional[str] = None,
    shipping: bool = None,
    time: Optional[str] = None,
    user_id: str = None,
    email: EmailStr = None
) -> dict:
    """
    Tool to update an existing order. Only `order_id` is required.
    Other fields will be updated if provided; otherwise, existing values are retained.
    """
    try:
        # Get a database session
        db = get_shop_db()
        
        try:
            # Find the existing order
            existing_order = db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
            
            if not existing_order:
                return {"error": f"Order '{order_id}' not found."}
                
            # Check if the order can be updated
            if existing_order.status != "Processing":
                return {f"Order '{order_id}' has already been processed. You can't update it."}
                
            quantity_int = existing_order.quantity
            
            # Update quantity if provided
            if quantity:
                try:
                    quantity_int = int(quantity)
                except ValueError:
                    return {"error": "Quantity must be a valid number."}
                    
                # Check stock if device_name is changed or quantity is updated
                check_device_name = device_name or existing_order.device_name
                item = db.query(Item).filter(Item.device_name == check_device_name).first()
                
                if not item:
                    return {"error": f"Device '{check_device_name}' not found in inventory."}
                    
                if item.in_store < quantity_int:
                    return {"error": f"Not enough stock for '{check_device_name}'."}
            
            # Update fields if provided
            if device_name:
                existing_order.device_name = device_name
            if address:
                existing_order.address = address
            if customer_name:
                existing_order.customer_name = customer_name
            if customer_phone:
                existing_order.customer_phone = customer_phone
            if quantity:
                existing_order.quantity = quantity_int
            if payment:
                existing_order.payment = payment
            if shipping is not None:
                existing_order.shipping = shipping
            if time:
                existing_order.time_reservation = time
            if user_id:
                existing_order.user_id = user_id
                
            # Recalculate price if quantity or device changed
            if quantity or device_name:
                item = db.query(Item).filter(Item.device_name == existing_order.device_name).first()
                existing_order.price = item.price * existing_order.quantity
                
            # Commit the changes
            db.commit()
            
            # Get updated values for the response
            updated = {
                "device_name": existing_order.device_name,
                "address": existing_order.address,
                "customer_name": existing_order.customer_name,
                "customer_phone": existing_order.customer_phone,
                "quantity": existing_order.quantity,
                "payment": existing_order.payment,
                "shipping": existing_order.shipping,
                "time_reservation": existing_order.time_reservation,
                "order_id": order_id,
                "price": existing_order.price
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        # Send email notification
        if email:
            email_subject = "Your FPT Shop Order Has Been Updated"
            email_body = f"""\
            Dear {updated["customer_name"]},

            Your order {order_id} has been successfully updated. Please review the latest order details below:

            🛒 Updated Order Details
            - Device Name: {updated["device_name"]}
            - Quantity: {updated["quantity"]}
            - Shipping Method: {updated["shipping"]}
            - Payment Method: {updated["payment"]}
            - Shipping Address: {updated["address"]}
            - Phone Number: {updated["customer_phone"]}
            - Reservation Time: {updated["time_reservation"]}

            💳 Updated Total: {updated["price"]}

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

            Kính gửi {updated["customer_name"]},

            Đơn hàng {order_id} của bạn đã được cập nhật thành công. Vui lòng kiểm tra thông tin mới nhất bên dưới:

            🛒 Thông tin đơn hàng cập nhật
            - Tên thiết bị: {updated["device_name"]}
            - Số lượng: {updated["quantity"]}
            - Phương thức vận chuyển: {updated["shipping"]}
            - Phương thức thanh toán: {updated["payment"]}
            - Địa chỉ giao hàng: {updated["address"]}
            - Số điện thoại: {updated["customer_phone"]}
            - Thời gian đặt hàng: {updated["time_reservation"]}

            💳 Tổng tiền sau cập nhật: {updated["price"]}

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
            "price": updated["price"],
            "message": f"Order {order_id} has been successfully updated. For more information please check your email."
        }

    except Exception as e:
        print(f"Error in update_order: {str(e)}")
        return {"error": f"Error updating order: {str(e)}"}

@tool("cancel_order", args_schema=CancelOrder)
def cancel_order(
    order_id: str,
    email: EmailStr = None
) -> str:
    """
    Tool to cancel order by order id
    """
    try:
        # Get a database session
        db = get_shop_db()
        
        try:
            # Find the order
            order = db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
            
            if not order:
                return f"Order with ID {order_id} not found."
                
            if order.status in ["Shipped", "Received", "Canceled", "Returned"]:
                return f"Cannot cancel order. Current status: {order.status}"
                
            customer_name = order.customer_name
            
            # Update the status
            order.status = "Canceled"
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
        # Send email notification
        if email:
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
                
            send_email(
                to_email=email,
                subject=email_subject,
                body=email_body
            )
            
        return f"Order {order_id} cancelled successfully."

    except Exception as e:
        return f"Error cancelling order: {str(e)}"

@tool("track_order", args_schema=TrackOrder)
def track_order(order_id: str) -> list[dict]:
    """
    Tool to track order info and status by order id
    """
    try:
        # Get a database session
        db = get_shop_db()
        
        try:
            # Find the order
            order = db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
            
            if not order:
                return f"Order with ID {order_id} not found."
                
            # Convert to dictionary for response
            result = {
                "order_id": order.order_id,
                "device_name": order.device_name,
                "address": order.address,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "quantity": order.quantity,
                "payment": order.payment,
                "shipping": order.shipping,
                "status": order.status,
                "time_reservation": order.time_reservation,
                "price": order.price,
                "user_id": order.user_id
            }
        finally:
            db.close()

        return result

    except Exception as e:
        return f"Error tracking order: {str(e)}"

