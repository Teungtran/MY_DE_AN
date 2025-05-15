import re


def clean_text(text: str) -> str:
    """
    Cleans and preprocesses text data.
    :param text: Raw text string.
    :return: Cleaned text string.
    """
    # Remove extra whitespace, newlines, and tabs
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    return cleaned_text
