from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def convert_to_string(val):
    if isinstance(val, str):
        return val
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, list):
        return " ".join(map(str, val))
    elif isinstance(val, dict):
        return " ".join(f"{k} {v}" for k, v in val.items())
    return ""

def calculate_similarities_batch(main_query: str, candidates: list, field: str) -> dict:
    """
    Compare user_input with each candidate's metadata[field] using TF-IDF + cosine similarity.
    candidates: list of Qdrant points
    """
    field_values = []
    for candidate in candidates:
        metadata = candidate.payload.get("metadata", {})
        field_value = convert_to_string(metadata.get(field, ""))
        field_values.append(field_value)

    if not field_values:
        return {}

    try:
        corpus = [main_query] + field_values
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(vectors[0], vectors[1:])[0]
        return {i: float(similarities[i]) for i in range(len(candidates))}
    except Exception as e:
        print(f"Similarity calculation failed: {e}")
        return {i: 0.0 for i in range(len(candidates))}