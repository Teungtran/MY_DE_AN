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
) -> Optional[List[Tuple[Dict, float, str]]]:
    """
    Full-scan version: returns ALL candidates that score >= 60,
    or the top 5 highest scoring candidates if none score >= 60.

    Enhanced:
    - Immediately return if any individual field value scores > 90
    - Return all candidates when 5 candidates score >= 60
    - Skip excluded fields
    - If no candidate meets min_score_threshold, return top 5 highest-scoring candidates (REUSING calculated scores)

    Returns: List of (candidate, score, matched_field) or None
    """
    if not candidates or not chunk.strip():
        return None

    if excluded_fields is None:
        excluded_fields = set()
    
    # Filter out excluded fields
    active_fields = [field for field in fields if field not in excluded_fields]
    
    if not active_fields:
        logger.info(f"[DEBUG] All fields excluded for chunk '{chunk}'. Skipping.")
        return None

    logger.info(f"\n[DEBUG] === FULL-SCAN Processing chunk: '{chunk}' ===")
    logger.info(f"[DEBUG] Active fields: {active_fields}")
    logger.info(f"[DEBUG] Excluded fields: {excluded_fields}")
    
    high_score_candidates = []  # List of (candidate, score, field) for score >= 60

    for candidate_idx, candidate in enumerate(candidates):
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

                # IMMEDIATE RETURN - Early exit on high score
                if score > 90.0:
                    logger.info(f"[DEBUG] *** EARLY RETURN *** Score {score:.1f} > 90 in field '{field}'")
                    early_result = [(candidate, score, field)]
                    return early_result

            if field_max_score > candidate_best_score:
                candidate_best_score = field_max_score
                candidate_best_field = field

        # Record for high-score tracking (>= 60)
        if candidate_best_score >= 60:
            high_score_candidates.append((candidate, candidate_best_score, candidate_best_field))

        # Early return if we have 5 high-scoring candidates
        if len(high_score_candidates) >= 5:
            logger.info(f"[DEBUG] Found {len(high_score_candidates)} candidates with score >= 60. Returning all.")
            high_score_candidates.sort(key=lambda x: x[1], reverse=True)
            return high_score_candidates

    # Case 1: Return high-score candidates if any found (>= 60)
    if high_score_candidates:
        logger.info(f"[DEBUG] Found {len(high_score_candidates)} candidates with score >= 60. Returning all.")
        high_score_candidates.sort(key=lambda x: x[1], reverse=True)
        return high_score_candidates
    
    logger.info(f"[DEBUG] No candidates >= 60 found for chunk '{chunk}'. Returning None (global fallback will handle this).")
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


