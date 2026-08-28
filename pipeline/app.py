"""
WORLD PULSE v6 - Application Pipeline

Orchestrates the independent processing layers:

articles
    ↓
normalize
    ↓
extract
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
from pipeline.intelligence import analyze_events
from pipeline.normalize import normalize_article
from pipeline.ranking import rank_events
from pipeline.verify import verify_events


def process_articles(articles):
    """
    Run the complete World Pulse v6 processing pipeline.

    This layer only connects the existing processing modules.
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

        if result and result.get("title"):
            normalized.append(result)

    if not normalized:
        return []

    clustered = cluster_articles(normalized)

    verified = verify_events(clustered)

    analyzed = analyze_events(verified)

    ranked = rank_events(analyzed)

    return ranked
