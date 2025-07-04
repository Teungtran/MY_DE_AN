from langchain_core.tools import tool
from rapidfuzz import process
from rapidfuzz.fuzz import partial_ratio,token_sort_ratio 
from collections import defaultdict
from pydantic import EmailStr
from typing import List, Dict, Optional, Tuple
from schemas.device_schemas import RecommendationConfig, CancelOrder, Order, TrackOrder, RecommendSystem, UpdateOrder
from .get_score import (
    calculate_similarities_batch, get_all_points, convert_to_string,determine_field_relevance)
from config.base_config import APP_CONFIG
import json
from .get_id import generate_short_id
from .send_email import send_order_confirmation,send_order_update,send_order_cancel
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


@tool("recommend_system", args_schema=RecommendSystem)
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
    main_query_lower = user_input.lower() if user_input else ""

    all_points_dict = get_all_points(type=type)

    # Merge preferences
    merged_pref = defaultdict(set)
    age_pref = get_other_preference(user_id)
    for source in [preference, age_pref]:
        for k, v in source.items():
            if isinstance(v, list):
                merged_pref[k].update(map(str.lower, v))
            else:
                merged_pref[k].add(str(v).lower())
    preference = {k: list(v) for k, v in merged_pref.items()}

    # Brand handling
    has_brands = False
    brands = []
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

    # Price handling
    price_input = [price] if price else []
    has_price_input = bool(price_input)

    price_min = price_max = None
    price_range = preference.get("price_range", []) if preference else []
    has_price = bool(price_range)
    if has_price:
        numeric_prices = []
        for p in price_range:
            try:
                numeric_prices.append(float(p))
            except (ValueError, TypeError):
                continue
        if numeric_prices:
            price_min = min(numeric_prices)
            price_max = max(numeric_prices)

    text_fields = [
        "device_name", "cpu", "card", "brand", "battery", 
        "storage", "discount_percent", "sales_price", "guarantee_program"
    ]

    final_results = {}  
    final_text_blocks = []

    if type == "get_all":
        for type_key, points_list in all_points_dict.items():
            print(f"\n>>> Processing get_all recommendations for type: {type_key} ({len(points_list)} points)")
            candidates = [{"doc": doc, "score": 0} for doc in points_list]

            if price_max:
                candidates = [
                    candidate for candidate in candidates
                    if isinstance(candidate["doc"].payload.get("metadata", {}).get("sale_price"), (int, float))
                    and candidate["doc"].payload.get("metadata", {}).get("sale_price") <= price_max * 1.2
                ]

            for candidate in candidates:
                meta = candidate["doc"].payload.get("metadata", {})
                sale_price = meta.get("sale_price")

                if has_brands:
                    doc_brand = meta.get("brand", "").lower()
                    best_match = process.extractOne(doc_brand, brands, scorer=partial_ratio)
                    best_brand_score = best_match[1] if best_match else 0

                    if best_brand_score >= 90:
                        candidate["score"] += recommendation_config.BRAND_MATCH_STRONG
                    elif best_brand_score >= 75:
                        candidate["score"] += recommendation_config.BRAND_MATCH_MEDIUM
                    elif best_brand_score >= 50:
                        candidate["score"] += recommendation_config.BRAND_MATCH_WEAK
                    else:
                        candidate["score"] += recommendation_config.BRAND_MISMATCH_PENALTY

                if has_price_input:
                    try:
                        price_number = float(price_input[0])
                        price_diff = abs(sale_price - price_number) / price_number
                        price_similarity = max(0, 1 - price_diff)
                        candidate["score"] += price_similarity * recommendation_config.PRICE_RANGE_MATCH_BOOST
                    except:
                        pass
                elif has_price:
                    if isinstance(sale_price, (int, float)):
                        if price_min is not None and price_max is not None and price_min <= sale_price <= price_max:
                            candidate["score"] += recommendation_config.PRICE_RANGE_MATCH_BOOST
                        elif price_max is not None and sale_price <= price_max:
                            candidate["score"] += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
                        elif price_min is not None and sale_price >= price_min:
                            candidate["score"] += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7

            top_match_count = min(recommendation_config.get_max_results(type_key), len(candidates))
            top_matches = heapq.nlargest(top_match_count, candidates, key=lambda x: x["score"])

            top_device_names = []
            for match in top_matches:
                device_name = match["doc"].payload.get("metadata", {}).get("device_name")
                if device_name:
                    top_device_names.append(device_name)

            final_results[type_key] = top_device_names

            if top_matches:
                meta_fields = [
                    "device_name", "cpu", "card", "screen", "storage", "image_link",
                    "sale_price", "discount_percent", "installment_price", "sales_perks", 
                    "guarantee_program", "payment_perks", "source"
                ]
                products_info = []
                for idx, item in enumerate(top_matches, start=1):
                    meta = item["doc"].payload.get("metadata", {})
                    content = f"Product {idx} (Score: {item['score']:.2f}) [{type_key}]:\n"
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
                final_text_blocks.append("\n".join(products_info))

        if not any(final_results.values()):
            return "I couldn't find any products matching your preferences.", []
        recommended_devices_cache = [d for devices in final_results.values() for d in devices]
        search_context = "\n\n".join(final_text_blocks)
        return search_context, recommended_devices_cache
    
    else:
        for type_key, points_list in all_points_dict.items():
            print(f"\n>>> Processing recommendations for type: {type_key} ({len(points_list)} points)")

            field_relevance = determine_field_relevance(main_query_lower, points_list, text_fields)
            print(f"Field relevance ranking: {field_relevance}")

            candidates = [{"doc": doc, "score": 0} for doc in points_list]

            if price_max:
                candidates = [
                    candidate for candidate in candidates
                    if isinstance(candidate["doc"].payload.get("metadata", {}).get("sale_price"), (int, float))
                    and candidate["doc"].payload.get("metadata", {}).get("sale_price") <= price_max * 1.2
                ]

            print(f"Starting with {len(candidates)} candidates after basic filtering")

            for stage_idx, (field, relevance_score) in enumerate(field_relevance):
                if len(candidates) <= 5:
                    break

                print(f"Stage {stage_idx + 1}: Filtering by '{field}' (relevance: {relevance_score:.2f})")
                
                similarities = calculate_similarities_batch(main_query_lower, candidates, field)
                
                field_scores = []
                for i, candidate in enumerate(candidates):
                    meta = candidate["doc"].payload.get("metadata", {})
                    field_value = convert_to_string(meta.get(field, ""))
                    
                    if not field_value:
                        fuzzy_score = 0
                        cosine_score = 0
                    else:
                        function = partial_ratio if len(main_query_lower.split()) < 5 else token_sort_ratio
                        fuzzy_score = function(main_query_lower, field_value.lower())
                        cosine_score = similarities.get(i, 0)
                    
                    combined_score = (
                        fuzzy_score * recommendation_config.FUZZY_WEIGHT + 
                        cosine_score * 100 * recommendation_config.COSINE_WEIGHT
                    )
                    field_scores.append((candidate, combined_score))

                field_scores.sort(key=lambda x: x[1], reverse=True)

                keep_ratio = [0.80, 0.65, 0.50, 0.35]
                keep_count = max(5, int(len(field_scores) * keep_ratio[min(stage_idx, 3)]))

                candidates = []
                for i, (candidate, field_score) in enumerate(field_scores[:keep_count]):
                    candidate["score"] += field_score * relevance_score * (1.0 / (stage_idx + 1))
                    candidates.append(candidate)

                print(f"After stage {stage_idx + 1}: {len(candidates)} candidates remaining")

            for candidate in candidates:
                meta = candidate["doc"].payload.get("metadata", {})
                sale_price = meta.get("sale_price")

                if has_brands:
                    doc_brand = meta.get("brand", "").lower()
                    best_match = process.extractOne(doc_brand, brands, scorer=partial_ratio)
                    best_brand_score = best_match[1] if best_match else 0

                    if best_brand_score >= 90:
                        candidate["score"] += recommendation_config.BRAND_MATCH_STRONG
                    elif best_brand_score >= 75:
                        candidate["score"] += recommendation_config.BRAND_MATCH_MEDIUM
                    elif best_brand_score >= 50:
                        candidate["score"] += recommendation_config.BRAND_MATCH_WEAK
                    else:
                        candidate["score"] += recommendation_config.BRAND_MISMATCH_PENALTY

                if has_price_input:
                    try:
                        price_number = float(price_input[0])
                        price_diff = abs(sale_price - price_number) / price_number
                        price_similarity = max(0, 1 - price_diff)
                        candidate["score"] += price_similarity * recommendation_config.PRICE_RANGE_MATCH_BOOST
                    except:
                        pass
                elif has_price:
                    if isinstance(sale_price, (int, float)):
                        if price_min is not None and price_max is not None and price_min <= sale_price <= price_max:
                            candidate["score"] += recommendation_config.PRICE_RANGE_MATCH_BOOST
                        elif price_max is not None and sale_price <= price_max:
                            candidate["score"] += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
                        elif price_min is not None and sale_price >= price_min:
                            candidate["score"] += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7

            top_match_count = min(recommendation_config.get_max_results(type_key), len(candidates))
            top_matches = heapq.nlargest(top_match_count, candidates, key=lambda x: x["score"])

            top_device_names = []
            for match in top_matches:
                device_name = match["doc"].payload.get("metadata", {}).get("device_name")
                if device_name:
                    top_device_names.append(device_name)

            final_results[type_key] = top_device_names

            if top_matches:
                meta_fields = [
                    "device_name", "cpu", "card", "screen", "storage", "image_link",
                    "sale_price", "discount_percent", "installment_price", "sales_perks", 
                    "guarantee_program", "payment_perks", "source"
                ]

                products_info = []
                for idx, item in enumerate(top_matches, start=1):
                    meta = item["doc"].payload.get("metadata", {})
                    content = f"Product {idx} (Score: {item['score']:.2f}) [{type_key}]:\n"
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
                final_text_blocks.append("\n".join(products_info))

        if not any(final_results.values()):
            return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

        search_context = "\n\n".join(final_text_blocks)
        recommended_devices_cache = [d for devices in final_results.values() for d in devices]

        print(f"Recommendation completed. Found {len(recommended_devices_cache)} products across {len(final_results)} type(s).")
        return search_context, recommended_devices_cache


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
                price=item.price * quantity_int 
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

        if email:
            email_subject, email_body = send_order_confirmation(customer_name, order_id, device_name, quantity_int, shipping, payment, address, customer_phone, time, order_price)
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
            email_subject, email_body = send_order_update(updated, order_id)
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
            
        if email:
            email_subject, email_body = send_order_cancel(order_id,customer_name)
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

