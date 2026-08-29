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
    ↓
editorial
"""

from pipeline.cluster import cluster_articles
from pipeline.content import build_contents
from pipeline.editorial import decide_events
from pipeline.extract import extract_facts
from pipeline.intelligence import analyze_events
from pipeline.normalize import normalize_article
from pipeline.publication import build_publications
from pipeline.ranking import rank_events
from pipeline.verify import verify_events


def process_articles(articles):
    """
    Run the complete World Pulse v6 processing pipeline.

    Returns the processed editorial events as a list.
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
        original_title = str(article.get("title", "")).strip()
        original_summary = str(article.get("summary", "")).strip()

        result = normalize_article(article)

        if not result or not result.get("title"):
            continue

        result["original_title"] = original_title
        result["original_summary"] = original_summary

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

    editorial = decide_events(ranked)

    content = build_contents(editorial)

    publication = build_publications(content)

    return publication


def build_edition_from_articles(articles):
    """
    Process articles and build a WORLD PULSE edition.
    """

    editorial = process_articles(articles)
