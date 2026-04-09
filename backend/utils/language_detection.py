import re

def detect_language(text: str) -> str:
    """
    Very basic heuristic language detection for transaction data.
    In a real app, you might use langdetect or fasttext.
    """
    if not text:
        return "Unknown"
        
    # Bengali unicode block: \u0980-\u09FF
    if re.search(r'[\u0980-\u09FF]', text):
        return "Bengali"
        
    # Odia unicode block: \u0B00-\u0B7F
    if re.search(r'[\u0B00-\u0B7F]', text):
        return "Odia"
        
    # Hindi/Devanagari unicode block: \u0900-\u097F
    if re.search(r'[\u0900-\u097F]', text):
        return "Hindi"
        
    # Default to English assuming standard Latin characters
    return "English"

def normalize_text(text: str) -> str:
    """
    Cleans up the transaction description text.
    """
    text = str(text).lower()
    # Remove extra spaces and special characters
    text = re.sub(r'[^a-zA-Z0-9\s\u0900-\u097F\u0980-\u09FF\u0B00-\u0B7F]', '', text)
    return text.strip()
