from typing_extensions import List, Dict, Optional, Set, Tuple
from ..support_funcs.supports import get_metadata,extract_all_text_from_field
from rapidfuzz.fuzz import token_set_ratio
from sklearn.feature_extraction.text import TfidfVectorizer
from app.utils.logging.logger import get_logger
from sklearn.neighbors import NearestNeighbors

logger = get_logger(__name__)

def extract_features(device_doc):
    """
    Extracts key-value pairs as strings from non-null feature metadata
    in the format: "key: value". Skips None or invalid entries.
    """
    features = []

    feature_blocks = [
        get_metadata(device_doc, "laptop_features", None),
        get_metadata(device_doc, "phone_features", None),
        get_metadata(device_doc, "tablet_features", None),
        get_metadata(device_doc, "brand", None),
        get_metadata(device_doc, "device_name", None),
    ]

    for block in feature_blocks:
        if not isinstance(block, dict):
            continue

        for key, value in block.items():
            if not value:
                continue

            if isinstance(value, str):
                value = value.strip()
                if value:
                    features.append(f"{key}: {value}")

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for sub_k, sub_v in item.items():
                            if sub_v:
                                features.append(f"{key}_{sub_k}: {str(sub_v).strip()}")
                    elif item:
                        features.append(f"{key}: {str(item).strip()}")

    return features
def get_best_candidate(
    chunk: str,
    candidates: List[Dict],
    fields: List[str],
    excluded_fields: Set[str] = None,
    device_name_mode: bool = False
) -> Optional[List[Tuple[Dict, float, str]]]:
    """
    Unified logic for both modes with configurable thresholds.
    
    DEVICE_NAME MODE (device_name_mode=True):
    - Early stop: >95
    - Scan all candidates, return top 5 (no minimum threshold)
    
    NORMAL MODE (device_name_mode=False):
    - Early stop: >90
    - Stop when 5 candidates score >=60
    - Return None if no candidates >=60

    Returns: List of (candidate, score, matched_field) or None
    """
    if not candidates or not chunk.strip():
        return None

    if excluded_fields is None:
        excluded_fields = set()
    
    active_fields = [field for field in fields if field not in excluded_fields]
    if not active_fields:
        logger.info(f"[DEBUG] All fields excluded for chunk '{chunk}'. Skipping.")
        return None

    # Configure thresholds based  mode
    config = {
        'early_stop': 100.0 if device_name_mode else 90.0,
        'min_score': None if device_name_mode else 60.0,  # None = no threshold
        'scan_all': device_name_mode,  # True = scan all, False = stop at 5
        'mode_label': "DEVICE_NAME" if device_name_mode else "NORMAL"
    }
    
    logger.info(f"\n[DEBUG] === FULL-SCAN [{config['mode_label']} MODE] Processing chunk: '{chunk}' ===")
    logger.info(f"[DEBUG] Early stop threshold: {config['early_stop']}")
    if config['min_score'] is not None:
        logger.info(f"[DEBUG] Min score threshold: {config['min_score']}")
    logger.info(f"[DEBUG] Scan all: {config['scan_all']}")
    logger.info(f"[DEBUG] Active fields: {active_fields}")
    
    candidate_scores = []  # Unified list for all scores

    for candidate_idx, candidate in enumerate(candidates):
        device_name = get_metadata(candidate["doc"], "device_name", "Unknown")
        logger.info(f"\n[DEBUG] --- Checking Candidate {candidate_idx + 1}: {device_name} ---")

        candidate_best_score = 0.0
        candidate_best_field = None

        for field in active_fields:
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

                # IMMEDIATE RETURN if score exceeds early stop threshold
                if score > config['early_stop']:
                    logger.info(f"[DEBUG] *** EARLY RETURN TRIGGERED *** Score {score} > {config['early_stop']} in field '{field}'")
                    return [(candidate, score, field)]

            if field_max_score > candidate_best_score:
                candidate_best_score = field_max_score
                candidate_best_field = field

        logger.info(f"[DEBUG] Candidate total score: {candidate_best_score} (best field: {candidate_best_field})")

        if config['min_score'] is None:
            # No threshold - collect all scores > 0
            if candidate_best_score > 0:
                candidate_scores.append((candidate, candidate_best_score, candidate_best_field))
        else:
            if candidate_best_score >= config['min_score']:
                candidate_scores.append((candidate, candidate_best_score, candidate_best_field))
                logger.info(f"[DEBUG] Candidate score >= {config['min_score']} (count: {len(candidate_scores)})")
                
                # Early return if we have 5 and not scanning all
                if not config['scan_all'] and len(candidate_scores) >= 5:
                    logger.info(f"[DEBUG] Found {len(candidate_scores)} candidates. Returning all.")
                    candidate_scores.sort(key=lambda x: x[1], reverse=True)
                    return candidate_scores

    # Return logic
    if candidate_scores:
        candidate_scores.sort(key=lambda x: x[1], reverse=True)
        top_5 = candidate_scores[:5]
        logger.info(f"[DEBUG] Scanned {len(candidate_scores)} candidates. Returning top {len(top_5)}:")
        for i, (cand, score, field) in enumerate(top_5, 1):
            name = get_metadata(cand["doc"], "device_name", "Unknown")
            logger.info(f"[DEBUG]   {i}. {name}: {score:.2f} (field: {field})")
        return top_5
    
    if config['min_score'] is not None:
        logger.info(f"[DEBUG] No candidates >= {config['min_score']} found. Returning None (fallback may trigger).")
    else:
        logger.info(f"[DEBUG] No candidates with score > 0 found.")
    return None




def suggest_similar_candidate(
    best_device: Dict,
    all_candidates: List[Dict],
    top_k: int = 5
) -> List[Dict]:
    try:
        best_device_name = get_metadata(best_device["doc"], "device_name", "")
    except Exception as e:
        logger.info(f"[DEBUG] Error accessing best device metadata: {e}")
        return []


    best_features = extract_features(best_device["doc"])
    best_feature_text = " ".join(best_features)

    candidates = []
    feature_texts = []

    for candidate in all_candidates:
        try:
            candidate_name = get_metadata(candidate["doc"], "device_name", "")
            if (
                candidate_name
                and candidate_name.strip() != best_device_name.strip()
            ):
                candidate_features = extract_features(candidate["doc"])
                feature_text = " ".join(candidate_features)
                candidates.append((candidate_name, candidate, feature_text))
                feature_texts.append(feature_text)
        except Exception as e:
            logger.info(f"[DEBUG] Error processing candidate: {e}")

    if not candidates:
        logger.info("[DEBUG] No suitable candidates after filtering.")
        return []

    # 1. TF-IDF on feature texts
    tfidf_vectorizer = TfidfVectorizer(
        lowercase=True,               
        stop_words=None,              
        max_features=2000,            
        min_df=1,                     
        max_df=0.95,                  
        norm='l2',                    
        sublinear_tf=True,            
        token_pattern=r"(?u)\b[\w\-/]+\b"  
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform([best_feature_text] + feature_texts)

    knn = NearestNeighbors(n_neighbors=min(top_k, len(candidates)), metric='cosine')
    knn.fit(tfidf_matrix[1:])  # Exclude best_device's features
    distances, indices = knn.kneighbors(tfidf_matrix[0], return_distance=True)

    final_scores = []
    for i, idx in enumerate(indices[0]):
        name, candidate, _ = candidates[idx]
        name_similarity = token_set_ratio(best_device_name, name) / 100.0
        feature_similarity = 1.0 - distances[0][i]  

        combined_score = 0.2 * name_similarity + 0.8 * feature_similarity
        final_scores.append((combined_score, candidate))

    # 4. Sort by combined score
    final_scores.sort(key=lambda x: x[0], reverse=True)

    # 5. Select top-k candidates
    top_candidates = [cand for _, cand in final_scores[:top_k]]

    logger.info(f"[DEBUG] Top {top_k} matched candidates:")
    for cand in top_candidates:
        logger.info(get_metadata(cand["doc"], "device_name", ""))

    return top_candidates

def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


