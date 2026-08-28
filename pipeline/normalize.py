"""
WORLD PULSE v6 - Text normalization layer.
"""

import re
import unicodedata


def normalize_text(value):
    """
    Normalize text consistently:
    - convert to string
    - Unicode normalize
    - lowercase
    - normalize dash variants to '-'
    - remove punctuation except hyphen
    - collapse whitespace
    """
    if value is None:
        return ""

    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()

    # Normalize common dash characters.
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", text)

    # Remove punctuation except hyphen.
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_source(value):
    """
    Normalize source names.
    """
    if value is None:
        return ""

    return normalize_text(value)


def normalize_article(article):
    """
    Normalize a news article without changing its structure.
    Invalid input returns an empty dictionary.
    """
    if not isinstance(article, dict):
        return {}

    result = dict(article)

    for field in (
        "title",
        "summary",
        "source",
        "category",
        "region",
    ):
        if field in result:
            result[field] = normalize_text(result[field])

    if "source" in result:
        result["source"] = normalize_source(result["source"])

    return result
