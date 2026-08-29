"""
WORLD PULSE v6 - Application Pipeline

Orchestrates the processing layers:

articles
    ↓
normalize
    ↓
extract facts
    ↓
cluster
    ↓
verification
    ↓
intelligence
    ↓
ranking
"""

from pipeline.cluster import cluster_articles
from pipeline.extract import extract_facts
from pipeline.intelligence import analyze_events
from pipeline.normalize import normalize_article
from pipeline.ranking import rank_events
from pipeline.verify import verify_events


def process_articles(articles):
    """
    Run the complete World Pulse v6 processing pipeline.
    """

    if not isinstance(articles, list):
        return []

    valid_articles = [
        article
        for article in articles
        if isinstance(article, dict)
        and article.get("title")
    ]

    if not valid_articles:
        return []

    normalized = []

    for article in valid_articles:
        result = normalize_article(article)

        if not result or not result.get("title"):
            continue

        facts = extract_facts(result)

        enriched = dict(result)

        enriched["event_types"] = facts.get(
            "event_types",
            [],
        )
        enriched["locations"] = facts.get(
            "locations",
            [],
        )
        enriched["actors"] = facts.get(
            "actors",
            [],
        )
        enriched["objects"] = facts.get(
            "objects",
            [],
        )
        enriched["numbers"] = facts.get(
            "numbers",
            [],
        )
        enriched["casualty_numbers"] = facts.get(
            "casualty_numbers",
            [],
        )

        normalized.append(enriched)

    if not normalized:
        return []

    clustered = cluster_articles(normalized)

    verified = verify_events(clustered)

    analyzed = analyze_events(verified)

    ranked = rank_events(analyzed)

    return ranked
