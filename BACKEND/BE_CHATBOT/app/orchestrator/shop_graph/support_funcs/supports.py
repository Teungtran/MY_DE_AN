from rapidfuzz.fuzz import token_set_ratio
from rapidfuzz import process
def get_metadata(doc, key, default=""):
    """Extract metadata from document with fallback to default"""
    try:
        if hasattr(doc, 'payload') and doc.payload:
            metadata = doc.payload.get('metadata', {})
            return metadata.get(key, default)
        return default
    except Exception as e:
        print(f"[DEBUG] Error getting metadata for key '{key}': {e}")
        return default
    
SUPPORTED_CATEGORIES = ["phone", "laptop/pc", "tablet"]
def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)

def normalize_type(d_type):
    d_type = d_type.lower().strip()
    result = process.extractOne(
        d_type,
        SUPPORTED_CATEGORIES,
        scorer=token_set_ratio,
        score_cutoff=60  
    )
    return result[0] 


def extract_all_text_from_field(field_value, field_name="", depth=0):
    """
    Recursively extract all text content from a field, handling nested structures.
    
    Args:
        field_value: Can be string, dict, list, or any combination
        field_name: Name of the field for debugging
        depth: Current recursion depth for indented printing
    
    Returns:
        List[str]: All text values found in the field
    """
    texts = []
    
    if isinstance(field_value, str):
        if field_value.strip():
            texts.append(field_value.strip())
    elif isinstance(field_value, dict):
        for key, value in field_value.items():
            if isinstance(value, str) and value.strip():
                combined_text = f"{key}: {value.strip()}"
                texts.append(combined_text)
            
            sub_texts = extract_all_text_from_field(value, f"{field_name}.{key}", depth + 1)
            texts.extend(sub_texts)
            
    elif isinstance(field_value, list):
        for i, item in enumerate(field_value):
            sub_texts = extract_all_text_from_field(item, f"{field_name}[{i}]", depth + 1)
            texts.extend(sub_texts)
    elif field_value is not None:
        text_val = str(field_value).strip()
        if text_val:
            texts.append(text_val)
    
    return texts    


