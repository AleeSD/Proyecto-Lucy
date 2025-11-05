import re
from typing import Dict, Any


def extract_entities(text: str) -> Dict[str, Any]:
    # Fallback regex-based NER for emails, urls, dates, mentions, hashtags, numbers
    entities = {
        "emails": re.findall(r"[\w\.\-]+@[\w\.-]+", text),
        "urls": re.findall(r"https?://[^\s]+", text),
        "dates": re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text),
        "mentions": re.findall(r"@([A-Za-z0-9_]+)", text),
        "hashtags": re.findall(r"#([A-Za-z0-9_]+)", text),
        "numbers": re.findall(r"\b\d+(?:\.\d+)?\b", text),
    }
    return entities