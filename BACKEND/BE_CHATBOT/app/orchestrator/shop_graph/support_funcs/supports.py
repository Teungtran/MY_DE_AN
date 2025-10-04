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
    Enhanced with debug prints to show extraction process.
    
    Args:
        field_value: Can be string, dict, list, or any combination
        field_name: Name of the field for debugging
        depth: Current recursion depth for indented printing
    
    Returns:
        List[str]: All text values found in the field
    """
    indent = "  " * depth
    texts = []
    
    print(f"{indent}[DEBUG] Extracting from field '{field_name}', type: {type(field_value)}")
    
    if isinstance(field_value, str):
        if field_value.strip():
            texts.append(field_value.strip())
            print(f"{indent}[DEBUG] Added string: '{field_value.strip()}'")
    elif isinstance(field_value, dict):
        print(f"{indent}[DEBUG] Processing dict with keys: {list(field_value.keys())}")
        for key, value in field_value.items():
            print(f"{indent}[DEBUG] Processing key: '{key}'")
            if isinstance(value, str) and value.strip():
                combined_text = f"{key}: {value.strip()}"
                texts.append(combined_text)
                print(f"{indent}[DEBUG] Added combined: '{combined_text}'")
            
            sub_texts = extract_all_text_from_field(value, f"{field_name}.{key}", depth + 1)
            texts.extend(sub_texts)
            
    elif isinstance(field_value, list):
        print(f"{indent}[DEBUG] Processing list with {len(field_value)} items")
        for i, item in enumerate(field_value):
            print(f"{indent}[DEBUG] Processing list item {i}")
            sub_texts = extract_all_text_from_field(item, f"{field_name}[{i}]", depth + 1)
            texts.extend(sub_texts)
    elif field_value is not None:
        text_val = str(field_value).strip()
        if text_val:
            texts.append(text_val)
            print(f"{indent}[DEBUG] Added converted: '{text_val}'")
    
    print(f"{indent}[DEBUG] Total texts extracted from '{field_name}': {len(texts)}")
    return texts    

import re
def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())
def count_words(text: str) -> int:
    return len(clean_text(text).split())


def merge_small_chunks(chunks, min_words=150):
    if not chunks:
        return []

    merged_chunks = [chunks[0]]
    
    for chunk in chunks[1:]:
        if count_words(chunk.page_content) < min_words:
            # Merge with previous
            merged_chunks[-1].page_content += " " + chunk.page_content
        else:
            merged_chunks.append(chunk)

    return merged_chunks

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
    
