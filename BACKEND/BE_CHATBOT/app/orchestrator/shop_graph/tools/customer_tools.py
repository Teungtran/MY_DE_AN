from langchain_core.tools import tool
from rapidfuzz.fuzz import token_set_ratio 
from pydantic import EmailStr
from typing import Optional, Tuple
from app.schemas.device_schemas import CancelOrder, Order, TrackOrder, RecommendSystem, UpdateOrder, DeviceDetailSchema
from ..support_funcs.get_candidates import get_all_points
from app.orchestrator.shop_graph.tools.hybrid_search import get_best_candidate, suggest_similar_candidate
from ..support_funcs.supports import get_metadata, extract_all_text_from_field
from langchain_community.retrievers import BM25Retriever
from app.services.get_retriever import get_device_retriever
from functools import lru_cache
import asyncio
import re
from ..support_funcs.get_id import generate_short_id
from app.services.inmemory_store import create_temporary_faiss_store,store_recommended_devices, clear_expired_recommendations,get_recommended_devices
from app.orchestrator.shop_graph.tools.send_email import send_order_confirmation,send_order_update,send_order_cancel
from app.utils.email import send_email
from app.models.database import  Order as OrderModel, Item, SessionLocal
from app.utils.logging.logger import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple, Set
from threading import Lock, Event


logger = get_logger(__name__)

def get_shop_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

current_device_faiss = None
def process_chunks_with_field_exclusion(
    chunks_to_process: List[str],
    candidates: List[Dict],
    all_fields: List[str],
    chunk_count: int,
    device_name_mode: bool = False  
) -> Tuple[List[Dict], List[Dict], Set[str]]:
    """
    Process ALL chunks in parallel with device_name priority support.
    
    DEVICE_NAME MODE (device_name_mode=True):
    - Early stop at >95, otherwise return top 5 from full scan
    - No global fallback needed (always returns results)
    
    NORMAL MODE (device_name_mode=False) - ORIGINAL BEHAVIOR:
    - Early stop at >90
    - Return candidates ≥60, stop when 5 found
    - Global fallback if no candidates ≥60 found
    
    Returns:
        strong_matches (≥early_stop_threshold),
        high_score_candidates (all returned candidates),
        excluded_fields
    """
    excluded_fields = set()
    excluded_fields_lock = Lock()
    strong_matches = []
    high_score_candidates = []
    results_lock = Lock()  # Unified lock for all result lists
    total_candidates_count = 0
    total_candidates_lock = Lock()
    early_stop_event = Event()  # Thread-safe event instead of dict
    
    all_candidate_scores = []  # For global fallback in normal mode
    all_scores_lock = Lock()

    # Set thresholds based on mode
    early_stop_threshold = 95.0 if device_name_mode else 90.0
    min_score_threshold = 70.0 if device_name_mode else 60.0  # For logging only
    
    mode_label = "DEVICE_NAME" if device_name_mode else "NORMAL"
    logger.info(f"[DEBUG:process_chunks] [{mode_label} MODE] Processing {chunk_count} chunks in parallel")
    logger.info(f"[DEBUG:process_chunks] Early stop threshold: {early_stop_threshold}")

    def process_chunk(chunk: str):
        nonlocal excluded_fields, strong_matches, high_score_candidates, total_candidates_count, all_candidate_scores

        try:
            # Check if we should stop early (thread-safe)
            if early_stop_event.is_set():
                logger.info(f"[DEBUG] Early stop triggered, skipping chunk: {chunk}")
                return

            # Get available fields (consider exclusions)
            with excluded_fields_lock:
                available_fields = [f for f in all_fields if f not in excluded_fields]
            if not available_fields:
                logger.info(f"[DEBUG] All fields excluded. Skipping chunk: {chunk}")
                return

            # Process this chunk independently with device_name_mode
            results = get_best_candidate(
                chunk=chunk,
                candidates=candidates,
                fields=available_fields,
                excluded_fields=excluded_fields,
                device_name_mode=device_name_mode  # Pass the mode
            )
            
            # NORMAL MODE: Collect fallback scores if no results (ORIGINAL BEHAVIOR)
            if not device_name_mode and not results:
                logger.info(f"[DEBUG] No results from get_best_candidate, collecting fallback scores for chunk '{chunk}'")
                chunk_fallback_scores = []
                try:
                    for candidate in candidates:
                        candidate_best_score = 0.0
                        candidate_best_field = None
                        
                        for field in available_fields:
                            try:
                                field_value = get_metadata(candidate["doc"], field)
                                if not field_value:
                                    continue

                                all_texts = extract_all_text_from_field(field_value, field)
                                if not all_texts:
                                    continue

                                field_max_score = 0.0
                                for text in all_texts:
                                    score = token_set_ratio(chunk.lower(), text.lower())
                                    field_max_score = max(field_max_score, score)

                                if field_max_score > candidate_best_score:
                                    candidate_best_score = field_max_score
                                    candidate_best_field = field
                            except Exception as e:
                                logger.warning(f"[DEBUG] Error processing field {field} for candidate: {e}")
                                continue
                        
                        if candidate_best_score > 0:
                            chunk_fallback_scores.append((candidate, candidate_best_score, candidate_best_field, chunk))
                    
                    with all_scores_lock:
                        all_candidate_scores.extend(chunk_fallback_scores)
                except Exception as e:
                    logger.error(f"[ERROR] Error collecting fallback scores for chunk '{chunk}': {e}", exc_info=True)
            elif results:
                logger.info(f"[DEBUG] get_best_candidate returned {len(results)} results")

            if not results:
                logger.info(f"[DEBUG] Chunk '{chunk}' found no candidates")
                return

            chunk_results = []
            for candidate, score, matched_field in results:
                item = {
                    "chunk": chunk,
                    "candidate": candidate,
                    "score": score,
                    "matched_field": matched_field
                }
                chunk_results.append(item)

            # Add to global results (thread-safe)
            with results_lock:
                for item in chunk_results:
                    high_score_candidates.append(item)
                    if item["score"] >= early_stop_threshold:
                        strong_matches.append(item)

            with total_candidates_lock:
                total_candidates_count += len(chunk_results)
                current_total = total_candidates_count

            logger.info(f"[DEBUG] Chunk '{chunk}' returned {len(chunk_results)} results (Total: {current_total})")

            # Stop when we have enough candidates (thread-safe)
            if current_total >= 5:
                logger.info(f"[DEBUG] Total candidates reached {current_total}, triggering early stop")
                early_stop_event.set()
        except Exception as e:
            logger.error(f"[ERROR] Error processing chunk '{chunk}': {e}", exc_info=True)

    logger.info("[DEBUG] Processing all chunks in parallel")
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks_to_process]
        
        for future in as_completed(futures):
            try:
                future.result()
                if early_stop_event.is_set():
                    logger.info("[DEBUG] Early stop triggered, canceling remaining futures")
                    for f in futures:
                        f.cancel()
                    break
            except Exception as e:
                logger.error(f"[ERROR] Error processing chunk in executor: {e}", exc_info=True)

    logger.info(f"[DEBUG] All chunks processed. Found {len(strong_matches)} strong matches (>={early_stop_threshold}), {len(high_score_candidates)} total candidates")
    
    # GLOBAL FALLBACK: ONLY for normal mode (ORIGINAL BEHAVIOR)
    if not device_name_mode and len(high_score_candidates) == 0 and all_candidate_scores:
        logger.info(f"[DEBUG] GLOBAL FALLBACK TRIGGERED: No chunks found candidates >= {min_score_threshold}. Selecting top 5 from all calculated scores.")
        
        all_candidate_scores.sort(key=lambda x: x[1], reverse=True)
        top_5_fallback = all_candidate_scores[:5]
        
        logger.info(f"[DEBUG] Global fallback - Top 5 candidates from {len(all_candidate_scores)} total scores:")
        
        for i, (candidate, score, matched_field, chunk) in enumerate(top_5_fallback, 1):
            fallback_item = {
                "chunk": chunk,
                "candidate": candidate,
                "score": score,
                "matched_field": matched_field
            }
            high_score_candidates.append(fallback_item)
            
            device_name = get_metadata(candidate["doc"], "device_name", "Unknown")
            logger.info(f"[DEBUG]   {i}. {device_name}: {score:.2f} (field: {matched_field}, chunk: {chunk})")
        
        logger.info(f"[DEBUG] Global fallback applied: {len(high_score_candidates)} candidates selected")
    elif len(high_score_candidates) > 0:
        logger.info(f"[DEBUG] Found {len(high_score_candidates)} candidates. No global fallback needed.")
    else:
        logger.info("[DEBUG] No candidates found and no fallback available.")

    return strong_matches, high_score_candidates, excluded_fields


async def scoring_logic(
    type_key,
    suitable_for,
    points_list,
    input_chunks,
    price_input,
    has_price_input,
    device_name,
    has_features,
    mandatory_fields,
    features_fields,
    supported_field
):
    """
    Improved scoring logic that always returns 10 candidates (5 best + 5 similar)
    and handles price filtering correctly.
    """
    try:
        logger.info(f"[DEBUG] Processing type: {type_key}, Devices: {len(points_list)}")

        # === Filtering: suitable_for and price ===
        filtered_points = points_list

        try:
            if suitable_for and suitable_for != "general":
                filtered_points = [
                    doc for doc in filtered_points
                    if get_metadata(doc, "suitable_for", "general") == suitable_for
                ]
                logger.info(f"[DEBUG] Filtered to {len(filtered_points)} devices for suitable_for={suitable_for}")
        except Exception as e:
            logger.error(f"[ERROR] Error filtering by suitable_for: {e}", exc_info=True)
            # Continue with original list

        # Price filtering logic - if price is provided, filter by it
        if has_price_input and price_input:
            try:
                max_price = float(price_input[0])
                filtered_points = [
                    doc for doc in filtered_points
                    if get_metadata(doc, "sale_price", 0) <= max_price
                ]
                logger.info(f"[DEBUG] Price filtered to {len(filtered_points)} devices under {max_price:,.0f} VND")
            except Exception as e:
                logger.warning(f"[WARNING] Price filter error: {e}, keeping all", exc_info=True)

        candidates = [{"doc": doc, "score": 0} for doc in filtered_points]
        original_candidates = candidates.copy()

        # === Determine fields ===
        text_fields = []
        try:
            if device_name and not has_features:
                text_fields = mandatory_fields
            elif has_features and not device_name:
                text_fields = features_fields + supported_field
            elif device_name and has_features:
                text_fields = mandatory_fields + features_fields
            text_fields = text_fields[:3]
            logger.info(f"[DEBUG] Processing fields: {text_fields}")
        except Exception as e:
            logger.error(f"[ERROR] Error determining fields: {e}", exc_info=True)
            text_fields = mandatory_fields[:3]  # Fallback

        # === Check if this is a price-only query (no features, no device_name) ===
        is_price_only_query = has_price_input and price_input and not has_features and not device_name
        
        if is_price_only_query:
            # Skip matching logic entirely for price-only queries
            logger.info("[DEBUG] PRICE-ONLY QUERY detected - skipping matching logic")
            final_candidates = candidates  # Use all filtered candidates
        else:
            try:
                # === Normal flow: Process chunks - get best candidates ===
                strong_matches, high_score_candidates, excluded_fields = process_chunks_with_field_exclusion(
                    input_chunks, candidates, text_fields, len(input_chunks),
                    device_name_mode=device_name
                )

                logger.info(f"[DEBUG] Final excluded fields: {excluded_fields}")
                logger.info(f"[DEBUG] Found {len(strong_matches)} strong matches")
                logger.info(f"[DEBUG] Found {len(high_score_candidates)} total candidates")

                # === Deduplicate by device_name and get top candidates ===
                device_scores = {}
                device_candidates = {}
                seen_names = set()

                try:
                    # Sort all candidates by score
                    all_relevant = sorted(high_score_candidates, key=lambda x: x["score"], reverse=True)

                    for item in all_relevant:
                        try:
                            cand = item["candidate"]
                            dev_name = get_metadata(cand["doc"], "device_name")
                            if dev_name and dev_name not in seen_names:
                                device_scores[dev_name] = item["score"]
                                device_candidates[dev_name] = cand
                                seen_names.add(dev_name)
                        except Exception as e:
                            logger.warning(f"[WARNING] Error processing candidate item: {e}")
                            continue

                    logger.info(f"[DEBUG] Found {len(seen_names)} unique devices from matching")

                    # === Build initial candidates list (top 5 from matching) ===
                    sorted_devices = sorted(device_scores.items(), key=lambda x: x[1], reverse=True)
                    top_5_matched = []
                    
                    for name, score in sorted_devices[:5]:  # Get only top 5
                        cand = device_candidates[name]
                        cand["score"] = score
                        top_5_matched.append(cand)

                    logger.info(f"[DEBUG] Selected top 5 from matching: {[get_metadata(c['doc'], 'device_name') for c in top_5_matched]}")

                    # === Get 5 similar candidates using similarity search ===
                    similar_candidates = []
                    existing_names = {get_metadata(c["doc"], "device_name", "") for c in top_5_matched}
                    
                    if top_5_matched:
                        try:
                            # Use the best matched candidate as reference for similarity
                            best_candidate = top_5_matched[0]
                            logger.info(f"[DEBUG] Finding similar products to: {get_metadata(best_candidate['doc'], 'device_name')}")
                            
                            # Get up to 10 similar candidates (we'll filter to 5 unique)
                            similar = suggest_similar_candidate(best_candidate, original_candidates, top_k=10)
                            
                            for sim_cand in similar:
                                try:
                                    name = get_metadata(sim_cand["doc"], "device_name", "")
                                    if name and name not in existing_names:
                                        similar_candidates.append(sim_cand)
                                        existing_names.add(name)
                                        if len(similar_candidates) >= 5:
                                            break
                                except Exception as e:
                                    logger.warning(f"[WARNING] Error processing similar candidate: {e}")
                                    continue
                            
                            logger.info(f"[DEBUG] Added {len(similar_candidates)} similar candidates")
                        except Exception as e:
                            logger.error(f"[ERROR] Error finding similar candidates: {e}", exc_info=True)

                    final_candidates = top_5_matched + similar_candidates
                    
                    unique_final = []
                    final_names = set()
                    for cand in final_candidates:
                        try:
                            name = get_metadata(cand["doc"], "device_name", "")
                            if name and name not in final_names:
                                unique_final.append(cand)
                                final_names.add(name)
                        except Exception as e:
                            logger.warning(f"[WARNING] Error deduplicating candidate: {e}")
                            continue
                    
                    final_candidates = unique_final
                    logger.info(f"[DEBUG] Final unique candidates: {len(final_candidates)}")
                except Exception as e:
                    logger.error(f"[ERROR] Error in candidate processing: {e}", exc_info=True)
                    final_candidates = []
            except Exception as e:
                logger.error(f"[ERROR] Error in process_chunks_with_field_exclusion: {e}", exc_info=True)
                final_candidates = []

        # === Pagination for large results (MEDIUM PRIORITY) ===
        MAX_RESULTS = 100  # Limit to prevent returning too many items
        should_return_all = has_price_input and price_input and not has_features and not device_name
        
        if should_return_all:
            # Pagination: Don't return 10,000 products at once!
            limited_points = filtered_points[:MAX_RESULTS]
            logger.info(f"[DEBUG] PRICE-ONLY QUERY - Returning {len(limited_points)} products (limited from {len(filtered_points)}) under price")
            top_matches = [{"doc": doc, "score": 0} for doc in limited_points]
            logger.info(f"[DEBUG] Total products returned: {len(top_matches)}")
        elif has_price_input and price_input:
            logger.info(f"[DEBUG] Price filter WITH features/device_name - returning top {min(len(final_candidates), MAX_RESULTS)} matched candidates")
            top_matches = final_candidates[:MAX_RESULTS]
        else:
            top_matches = final_candidates[:10]  # Limit to 10 otherwise
            logger.info(f"[DEBUG] No price filter - returning top {len(top_matches)} candidates")

        # === Build device names list ===
        top_device_names = []
        try:
            for m in top_matches:
                try:
                    name = get_metadata(m["doc"], "device_name")
                    if name:
                        top_device_names.append(name)
                except Exception as e:
                    logger.warning(f"[WARNING] Error extracting device name: {e}")
                    continue
        except Exception as e:
            logger.error(f"[ERROR] Error building device names list: {e}", exc_info=True)

        # === Build product info block ===
        product_info_block = ""
        try:
            if top_matches:
                meta_fields = [
                    "device_name", "laptop_features", "phone_features", "tablet_features",
                    "image_link", "sale_price", "all_perks", "source"
                ]
                products_info = []
                for idx, item in enumerate(top_matches, start=1):
                    try:
                        score = item.get('score', 0)
                        content = f"Product {idx} (Score: {score:.2f}) [{type_key}]:\n"
                        for field in meta_fields:
                            try:
                                value = get_metadata(item["doc"], field, "")
                                content += f"- {field}: {value}\n"
                            except Exception as e:
                                logger.warning(f"[WARNING] Error getting field {field}: {e}")
                                content += f"- {field}: N/A\n"
                        products_info.append(content)
                    except Exception as e:
                        logger.warning(f"[WARNING] Error formatting product {idx}: {e}")
                        continue
                product_info_block = "\n".join(products_info)
        except Exception as e:
            logger.error(f"[ERROR] Error building product info block: {e}", exc_info=True)

        return type_key, top_device_names, product_info_block, top_matches
    
    except Exception as e:
        logger.error(f"[ERROR] Scoring logic failed for type {type_key}: {e}", exc_info=True)
        # Graceful failure - return empty results
        return type_key, [], "", []

def parse_structured_input(structured_input):
    """
    Parse structured input:
    1. First split by commas.
    2. If fewer than 2 chunks are found, fallback to 4-word chunks.
    3. Shuffle the resulting chunks randomly.
    """
    comma_chunks = [chunk.strip() for chunk in structured_input.split(',') if chunk.strip()]
    
    if len(comma_chunks) >= 1:
        return comma_chunks

    chunks = []
    words = structured_input.split()
    chunk = []

    for word in words:
        chunk.append(word)
        if len(chunk) == 3:
            chunks.append(' '.join(chunk))
            chunk = []

    if chunk:
        chunks.append(' '.join(chunk))
    return chunks  

async def recommend_system_async(
    user_input: List[str],
    suitable_for: str,
    device_name: bool = False,
    has_features: bool = False,
    device_type: str = None,
    price: str = None
) -> Tuple[str, List[str]]:
    """
    Optimized recommendation system with parallel processing and field-level early stopping.
    """
    clear_expired_recommendations()
    price_input = [price] if price else []
    logger.info(f"[DEBUG] Price input: {price_input}")
    has_price_input = bool(price_input)
    all_points_dict = get_all_points(device_type=device_type)
    logger.info(f"[DEBUG] Suitable for: {suitable_for}")
    logger.info(f"[DEBUG] Types found in all_points_dict: {list(all_points_dict.keys())}")
    mandatory_fields = ["device_name"]  
    feature_fields = ["phone_features", "laptop_features", "tablet_features"]
    best_field, best_score = max(
        ((field, token_set_ratio(device_type, field)) for field in feature_fields),
        key=lambda x: x[1]
    )
    
    brand_field = ["brand"]
    input_chunks = parse_structured_input(user_input)
    tasks = [
        scoring_logic(
            type_key=type_key,
            suitable_for=suitable_for,
            points_list = points_list,
            has_features=has_features,
            has_price_input=has_price_input,
            mandatory_fields=mandatory_fields,
            features_fields=[best_field],
            supported_field=brand_field,
            input_chunks = input_chunks,
            price_input=price_input,
            device_name = device_name
        )
        for type_key, points_list in all_points_dict.items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Combine results
    final_results = {}
    final_text_blocks = []
    all_top_candidates = []  # Collect all candidate objects
    
    for result in results:
        if len(result) == 4: 
            type_key, device_names, info_block, top_candidates = result
            all_top_candidates.extend(top_candidates)
        else:  
            type_key, device_names, info_block = result
            
        final_results[type_key] = device_names
        if info_block:
            final_text_blocks.append(info_block)
            logger.info(f"[DEBUG] Added info_block for {type_key}: {len(info_block)} chars")
        else:
            logger.warning(f"[WARNING] Empty info_block for {type_key} despite having {len(device_names)} devices!")

    if not any(final_results.values()):
        return "I couldn't find any products matching your criteria.", []

    recommended_devices = [d for devices in final_results.values() for d in devices]
    store_recommended_devices(recommended_devices, user_input)    
    
    if all_top_candidates:
        try:
            faiss_store = create_temporary_faiss_store(top_matches=all_top_candidates)
            global current_device_faiss
            current_device_faiss = faiss_store
            logger.info(f"[DEBUG] Created FAISS store with {len(all_top_candidates)} candidates")
        except ImportError as e:
            logger.warning(f"[WARNING] FAISS not available: {e}. Device details feature will be limited.")
            current_device_faiss = None
        except Exception as e:
            logger.error(f"[ERROR] Failed to create FAISS store: {e}")
            current_device_faiss = None
    else:
        logger.info("[DEBUG] No top candidates available for FAISS store creation")
    
    final_response = "\n\n".join(final_text_blocks)
    logger.info(f"[DEBUG] Returning response with {len(final_text_blocks)} text blocks, total length: {len(final_response)}")
    logger.info(f"[DEBUG] Recommended devices: {recommended_devices}")
    return final_response, recommended_devices

@tool("recommend_system",args_schema=RecommendSystem)
def recommend_system(user_input: str, device_name:bool,has_features:bool, device_type: str = None, price: str = None, suitable_for: str = None):
    """
    Recommend products based on user input, type , and suitable_for use cases.
    THIS tool is a preset tool, you should always call this tool when you need to recommend products and before you call device_details tool.
    """
    logger.info(f"[TOOL ENTRY] recommend_system called with: user_input={user_input[:100]}, device_type={device_type}, price={price}, suitable_for={suitable_for}")
    if not price:
        match = re.search(r"price:\s*([0-9]+)", user_input)
        if match:
            price = match.group(1)
    
    if not suitable_for:
        suitable_for_match = re.search(r"suitable_for:\s*([^,\n]+)", user_input)
        if suitable_for_match:
            suitable_for = suitable_for_match.group(1).strip()
        else:
            suitable_for = "general"
    
    response_text, device_list = asyncio.run(recommend_system_async(
        user_input=user_input,
        suitable_for=suitable_for,
        device_name=device_name,
        has_features=has_features,
        device_type=device_type,
        price=price
    ))
    logger.info(f"[TOOL EXIT] recommend_system returning: response_length={len(response_text)}, devices={device_list}")
    return response_text
    
@lru_cache(maxsize=1000)
def cached_faiss_retrieve(query: str,faiss_store):
    retriever = get_device_retriever(faiss_store)
    return retriever.get_relevant_documents(query)


@tool("get_device_details", args_schema=DeviceDetailSchema)
def get_device_details(user_input: str, device_name, count_devices: int) -> str:
    """
    Retrieve detailed information about a specific device.
    This tool is not a preset tool, you should not call this tool FIRST.
    """
    try:
        clear_expired_recommendations()
        cached_result = get_recommended_devices()

        if not cached_result:
            return "No recent recommendations found. Please use the recommend_system tool first."

        device_names, _, _ = cached_result
        logger.info(f"Available devices: {device_names}")

        if device_name:
            scored_devices = [
                (rec_device, token_set_ratio(user_input.lower(), rec_device.lower()))
                for rec_device in device_names
            ]
            if not scored_devices:
                return "No matching devices found. Try using the full device name."
            scored_devices.sort(key=lambda x: x[1], reverse=True)
            top_device, top_score = scored_devices[0]
            logger.info(f"Top matched device: {top_device} (score: {top_score})")
        else:
            top_device = device_names[0]
            logger.info(f"Using first device from cache: {top_device}")

        global current_device_faiss
        if current_device_faiss is None:
            return "Session expired or device data unavailable. Please search again."

        results = []

        if count_devices == 1:
            if device_name:
                scored_devices = [
                    (rec_device, token_set_ratio(user_input.lower(), rec_device.lower()))
                    for rec_device in device_names
                ]
                if not scored_devices:
                    return "No matching devices found. Try using the full device name."
                scored_devices.sort(key=lambda x: x[1], reverse=True)
                top_device, _ = scored_devices[0]
            else:
                top_device = device_names[0]

            query = f"{user_input} {top_device}"
            all_chunks = cached_faiss_retrieve(query, current_device_faiss)
            results.append((top_device, all_chunks))

        else:
            for top_device in device_names:
                query = f"{user_input}"
                all_chunks = cached_faiss_retrieve(query, current_device_faiss)
                results.append((top_device, all_chunks))

        final_output = []

        for _, chunks in results:
            unique_chunks = []
            seen_content = set()
            for chunk in chunks:
                content_hash = hash(chunk.page_content.strip())
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_chunks.append(chunk)

            bm25_retriever = BM25Retriever.from_documents(unique_chunks, k=len(unique_chunks))
            bm25_results = bm25_retriever.get_relevant_documents(f"{user_input}")
            top_chunks = bm25_results[:5]
            chunk_texts = "\n\n---\n\n".join([doc.page_content for doc in top_chunks])
            final_output.append(f"### Top Relevant Content for `{user_input}`:\n\n{chunk_texts}")

        return "\n\n\n".join(final_output)

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
        logger.info(f"Error in order_purchase: {str(e)}")
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
        logger.info(f"Error in update_order: {str(e)}")
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

