import re
from typing import Dict, Tuple


def normalize_text(text: str) -> set:
    """Lowercase + remove punctuation + tokenize"""
    if not text:
        return set()
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return set(text.split())


def text_similarity(a: str, b: str) -> float:
    """Jaccard similarity on word tokens"""
    tokens_a = normalize_text(a)
    tokens_b = normalize_text(b)

    if not tokens_a or not tokens_b:
        return 0.0

    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def list_similarity(a: list, b: list) -> float:
    """Jaccard similarity for lists"""
    set_a = set(map(str.lower, a or []))
    set_b = set(map(str.lower, b or []))

    if not set_a or not set_b:
        return 0.0

    return len(set_a & set_b) / len(set_a | set_b)