import re

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())
def count_words(text: str) -> int:
    return len(clean_text(text).split())