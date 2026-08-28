# =========================================================
# WORLD PULSE v6 — TEXT NORMALIZATION
# =========================================================

import re
import unicodedata


def normalize_text(value):
    """
    Normalize text for deterministic processing.

    This function does NOT classify events.
    It does NOT calculate similarity.
    It only cleans text.
    """

    if value is None:
        return ""

    text = str(value)

    # Unicode normalization
    text = unicodedata.normalize(
        "NFKC",
        text
    )

    # Lowercase
    text = text.lower()

    # Normalize common dash variants
    text = (
        text
        .replace("–", "-")
        .replace("—", "-")
        .replace("-", "-")
        .replace("_", " ")
    )

    # Remove URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    # Keep letters/numbers/spaces
    # Unicode-aware: Cyrillic and other languages remain intact.
    text = re.sub(
        r"[^\w\s-]",
        " ",
        text,
        flags=re.UNICODE
    )

    # Collapse whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_source(value):
    """
    Normalize source name.
    """

    return normalize_text(value)


def normalize_article(article):
    """
    Return a normalized copy of an article.
    """

    if not isinstance(article, dict):
        return {}

    result = dict(article)

    result["title"] = normalize_text(
        article.get("title", "")
    )

    result["summary"] = normalize_text(
        article.get("summary", "")
    )

    result["source"] = normalize_source(
        article.get("source", "")
    )

    result["category"] = normalize_text(
        article.get("category", "")
    )

    result["region"] = normalize_text(
        article.get("region", "")
    )

    return result
