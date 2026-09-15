"""
AROUND THE MAIN v6 - Source Chain

Measures source provenance and independence.

This layer does not determine whether an event is true.
It determines how many genuinely independent information
origins appear to support an event.
"""

from __future__ import annotations

from typing import Any


DERIVATION_RELATIONS = {
    "original",
    "official_statement",
    "direct_report",
    "republished",
    "syndicated",
    "aggregated",
    "unknown",
}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


SOURCE_ALIASES = {
    "reuters": "reuters",
    "reuters news": "reuters",
    "thomson reuters": "reuters",

    "associated press": "ap",
    "ap news": "ap",
    "ap": "ap",

    "agence france presse": "afp",
    "afp": "afp",

    "bbc news": "bbc",
    "bbc world": "bbc",
    "bbc": "bbc",

    "un news": "un",
    "un news centre": "un",
    "un": "un",
}


def _canonical_source_name(value: Any) -> str:
    name = _safe_text(value)

    if not name:
        return ""

    return SOURCE_ALIASES.get(name, name)


def _source_name(article: dict) -> str:
    if not isinstance(article, dict):
        return ""

    return _canonical_source_name(
        article.get("source")
        or article.get("publisher")
        or article.get("source_name")
    )


def _source_id(article: dict) -> str:
    if not isinstance(article, dict):
        return ""

    value = (
        article.get("source_id")
        or article.get("publisher_id")
        or article.get("source")
    )

    return _canonical_source_name(value)


def _canonical_source(article: dict) -> str:
    """Return a normalized publisher identity."""
    source = _source_name(article)

    aliases = {
        "reuters": "reuters",
        "reuters news": "reuters",
        "thomson reuters": "reuters",
        "associated press": "ap",
        "ap news": "ap",
        "ap": "ap",
        "agence france presse": "afp",
        "afp": "afp",
        "bbc news": "bbc",
        "bbc world": "bbc",
        "bbc": "bbc",
        "un news": "un",
        "un news centre": "un",
        "un": "un",
    }

    return aliases.get(source, source)


def _relation(article: dict) -> str:
    if not isinstance(article, dict):
        return "unknown"

    value = _safe_text(
        article.get("derivation")
        or article.get("source_relation")
        or article.get("relation")
    )

    if value in DERIVATION_RELATIONS:
        return value

    return "unknown"


def _origin(article: dict) -> str:
    if not isinstance(article, dict):
        return ""

    value = (
        article.get("origin_source")
        or article.get("original_source")
        or article.get("origin")
    )

    return _safe_text(value)


def _canonical_origin(article: dict) -> str:
    """
    Determine the best available information origin.
    """

    origin = _origin(article)

    if origin:
        return origin

    relation = _relation(article)

    if relation in {
        "original",
        "official_statement",
        "direct_report",
    }:
        return _source_id(article)

    return ""


def same_source(a: dict, b: dict) -> bool:
    """
    Return True when two articles appear to come from
    the same publisher.
    """

    source_a = _canonical_source(a)
    source_b = _canonical_source(b)

    return bool(
        source_a
        and source_b
        and source_a == source_b
    )


def same_origin(a: dict, b: dict) -> bool:
    """
    Return True when two articles explicitly identify
    the same original information source.
    """

    origin_a = _canonical_origin(a)
    origin_b = _canonical_origin(b)

    if not origin_a or not origin_b:
        return False

    return origin_a == origin_b


def is_independent(a: dict, b: dict) -> bool:
    """
    Conservative pairwise independence test.
    """

    if not isinstance(a, dict):
        return False

    if not isinstance(b, dict):
        return False

    if same_source(a, b):
        return False

    if same_origin(a, b):
        return False

    relation_a = _relation(a)
    relation_b = _relation(b)

    source_a = _source_id(a)
    source_b = _source_id(b)

    origin_a = _origin(a)
    origin_b = _origin(b)

    if relation_a in {
        "republished",
        "syndicated",
        "aggregated",
    }:
        if source_b and origin_a == source_b:
            return False

    if relation_b in {
        "republished",
        "syndicated",
        "aggregated",
    }:
        if source_a and origin_b == source_a:
            return False

    return True


def independent_source_groups(
    articles: list[dict],
) -> list[list[dict]]:
    """
    Group articles that share a known information origin.

    Unknown provenance remains separate rather than being
    incorrectly treated as a shared origin.
    """

    if not isinstance(articles, list):
        return []

    groups: list[list[dict]] = []
    known_origins: dict[str, list[dict]] = {}
    for article in articles:
        if not isinstance(article, dict):
            continue

        origin = _canonical_origin(article)

        if origin:
            if origin not in known_origins:
                known_origins[origin] = []

            known_origins[origin].append(article)
        else:
            groups.append([article])

    groups.extend(known_origins.values())

    return groups


def count_independent_sources(
    articles: list[dict],
) -> int:
    """
    Count distinct information origins.

    Same publisher counts once.

    Multiple publishers explicitly deriving from the same
    origin count once.

    Unknown provenance is counted conservatively by publisher.
    """

    if not isinstance(articles, list):
        return 0

    origins: set[str] = set()
    publishers: set[str] = set()

    for article in articles:
        if not isinstance(article, dict):
            continue

        origin = _canonical_origin(article)

        if origin:
            origins.add(origin)
            continue

        source = (
            _canonical_source(article)
            or _source_id(article)
        )

        if source:
            publishers.add(source)

    return len(origins | publishers)


def source_chain_summary(
    articles: list[dict],
) -> dict:
    """
    Return a compact source-chain summary.
    """

    if not isinstance(articles, list):
        articles = []

    valid_articles = [
        article
        for article in articles
        if isinstance(article, dict)
    ]

    independent_sources = count_independent_sources(
        valid_articles
    )

    known_origins = sorted(
        {
            _canonical_origin(article)
            for article in valid_articles
            if _canonical_origin(article)
        }
    )

    publishers = sorted(
        {
            _source_name(article)
            for article in valid_articles
            if _source_name(article)
        }
    )

    relations = sorted(
        {
            _relation(article)
            for article in valid_articles
        }
    )

    if independent_sources >= 3:
        confidence = "HIGH"
    elif independent_sources == 2:
        confidence = "MEDIUM"
    elif independent_sources == 1:
        confidence = "LOW"
    else:
        confidence = "UNKNOWN"

    return {
        "article_count": len(valid_articles),
        "publisher_count": len(publishers),
        "independent_sources": independent_sources,
        "known_origins": known_origins,
        "relations": relations,
        "independence_confidence": confidence,
    }


def analyze_source_chain(event: dict) -> dict:
    """
    Analyze source independence for an event.

    The event is never modified.
    """

    if not isinstance(event, dict):
        return source_chain_summary([])

    return source_chain_summary(
        event.get("articles", [])
    )
