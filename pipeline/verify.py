"""
AROUND THE MAIN v6 - Verification Layer

Evaluates how strongly an event is independently corroborated.

Verification is deliberately separate from:
- extraction
- clustering
- intelligence
- editorial ranking
"""

from collections import Counter
from typing import Any

from pipeline.source_chain import analyze_source_chain


UNCONFIRMED = "UNCONFIRMED"
SINGLE_SOURCE = "SINGLE_SOURCE"
MULTI_SOURCE = "MULTI_SOURCE"
WIDELY_CONFIRMED = "WIDELY_CONFIRMED"


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    return []


def _normalize_name(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def _unique(values: list[Any]) -> list[str]:
    result = []

    for value in values:
        normalized = _normalize_name(value)

        if normalized and normalized not in result:
            result.append(normalized)

    return sorted(result)


def _articles(event: Any) -> list[dict]:
    if not isinstance(event, dict):
        return []

    articles = event.get("articles")

    if not isinstance(articles, list):
        return []

    return [
        article
        for article in articles
        if isinstance(article, dict)
    ]


def _sources(articles: list[dict]) -> list[str]:
    return _unique([
        article.get("source")
        for article in articles
    ])


def _categories(articles: list[dict]) -> list[str]:
    return _unique([
        article.get("category")
        for article in articles
    ])


def _regions(articles: list[dict]) -> list[str]:
    return _unique([
        article.get("region")
        for article in articles
    ])


def _countries(articles: list[dict]) -> list[str]:
    countries = []

    for article in articles:
        value = article.get("country")

        if value:
            countries.append(value)

    return _unique(countries)


def _source_groups(sources: list[str]) -> list[str]:
    """
    Map obvious aliases/syndication names to one parent group.

    Unknown sources remain independent by default.
    """

    aliases = {
        "reuters news": "reuters",
        "reuters": "reuters",
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

    return sorted({
        aliases.get(source, source)
        for source in sources
    })


def _agreement(event: dict, articles: list[dict]) -> float:
    """
    Estimate agreement between reports.

    The clusterer has already established that the articles belong
    to the same event. Here we use the available cluster similarity
    scores plus structural agreement.

    Empty/malformed data receives a safe low-confidence value.
    """

    if not articles:
        return 0.0

    scores = [
        float(value)
        for value in _safe_list(event.get("similarity_scores"))
        if isinstance(value, (int, float))
    ]

    similarity = (
        sum(scores) / len(scores)
        if scores
        else 1.0
    )

    # Structural agreement.
    titles = [
        _normalize_name(article.get("title"))
        for article in articles
        if article.get("title")
    ]

    source_count = len(_sources(articles))
    category_count = len(_categories(articles))

    structural = 1.0

    if not titles:
        structural *= 0.50

    if category_count > 1:
        structural *= 0.90

    if source_count > 1:
        structural *= 1.00

    agreement = (
        similarity * 0.70
        + structural * 0.30
    )

    return round(
        max(0.0, min(1.0, agreement)),
        4,
    )
def _verification_score(
    independent_source_count: int,
    agreement: float,
    source_diversity: int,
    country_diversity: int,
    region_diversity: int,
    category_diversity: int,
) -> float:
    """
    Verification score is NOT editorial significance.

    It measures corroboration strength only.
    """

    if independent_source_count <= 0:
        return 0.0

    # Independent source contribution.
    source_score = min(
        independent_source_count,
        5,
    ) / 5.0

    # Diversity is supporting evidence, not a substitute for sources.
    diversity_bonus = min(
        1.0,
        (
            max(0, source_diversity - 1) * 0.05
            + max(0, country_diversity - 1) * 0.05
            + max(0, region_diversity - 1) * 0.05
            + max(0, category_diversity - 1) * 0.05
        ),
    )

    score = (
        source_score * 0.60
        + agreement * 0.30
        + diversity_bonus * 0.10
    )

    return round(
        max(0.0, min(1.0, score)) * 100.0,
        2,
    )


def verification_level(
    independent_source_count: int,
    agreement: float,
) -> str:
    """
    Determine verification level from independent corroboration.

    A single source can never become MULTI_SOURCE merely because
    its article has high similarity.
    """

    if independent_source_count <= 0:
        return UNCONFIRMED

    if independent_source_count == 1:
        return SINGLE_SOURCE

    if independent_source_count == 2:
        return MULTI_SOURCE

    if independent_source_count >= 3 and agreement >= 0.55:
        return WIDELY_CONFIRMED

    return MULTI_SOURCE


def verify_event(event: Any) -> dict:
    """
    Verify one clustered event.

    Returns a stable dictionary and never raises for malformed input.
    """

    if not isinstance(event, dict):
        return {
            "verification_level": UNCONFIRMED,
            "verification_score": 0.0,
            "sources": [],
            "independent_sources": 0,
            "source_groups": [],
            "countries": [],
            "regions": [],
            "categories": [],
            "agreement": 0.0,
            "article_count": 0,
        }

    articles = _articles(event)

    if not articles:
        return {
            "verification_level": UNCONFIRMED,
            "verification_score": 0.0,
            "sources": [],
            "independent_sources": 0,
            "source_groups": [],
            "countries": [],
            "regions": [],
            "categories": [],
            "agreement": 0.0,
            "article_count": 0,
        }

    sources = _sources(articles)
    source_groups = _source_groups(sources)
    source_chain = analyze_source_chain(event)

    countries = _countries(articles)
    regions = _regions(articles)
    categories = _categories(articles)

    agreement = _agreement(
        event,
        articles,
    )

    independent_source_count = source_chain["independent_sources"]
    level = verification_level(
        independent_source_count,
        agreement,
    )


    score = _verification_score(
        independent_source_count=independent_source_count,
        agreement=agreement,
        source_diversity=len(source_groups),
        country_diversity=len(countries),
        region_diversity=len(regions),
        category_diversity=len(categories),
    )

    return {
        "verification_level": level,
        "verification_score": score,
        "sources": sources,
        "independent_sources": independent_source_count,
        "source_groups": source_groups,
        "source_chain": source_chain,
        "countries": countries,
        "regions": regions,
        "categories": categories,
        "agreement": agreement,
        "article_count": len(articles),
    }


def verify_events(events: Any) -> list[dict]:
    """
    Verify a collection of clustered events.
    """

    if not isinstance(events, list):
        return []

    results = []

    for event in events:
        if not isinstance(event, dict):
            continue

        verification = verify_event(event)

        result = dict(event)
        result["verification"] = verification

        results.append(result)

    return results
