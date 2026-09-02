"""
AROUND THE MAIN v6 - Application Pipeline

Orchestrates the processing layers:

articles
    ↓
editorial snapshot eligibility
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
from datetime import datetime, time
from zoneinfo import ZoneInfo

from pipeline.event_memory import EventMemory
from pipeline.cluster import cluster_articles
from pipeline.content import build_contents
from pipeline.delivery import build_deliveries
from pipeline.edition import build_edition
from pipeline.edition_id import DEFAULT_TIMEZONE
from pipeline.editorial import decide_events
from pipeline.editorial_snapshot import filter_events_for_snapshot
from pipeline.extract import extract_facts
from pipeline.intelligence import analyze_events
from pipeline.normalize import normalize_article
from pipeline.publication import build_publications
from pipeline.ranking import rank_events
from pipeline.verify import verify_events


EDITORIAL_TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE)


def _build_editorial_time(publication_date, edition_time):
    """Build the canonical local editorial snapshot datetime."""

    if publication_date is None or edition_time is None:
        return None

    if isinstance(publication_date, datetime):
        local_date = publication_date.astimezone(
            EDITORIAL_TIMEZONE
        ).date()
    else:
        text = str(publication_date).strip()
        try:
            local_date = datetime.fromisoformat(text).date()
        except ValueError:
            return None

    try:
        hour, minute = (
            int(part)
            for part in str(edition_time).split(":", 1)
        )
    except (TypeError, ValueError):
        return None

    return datetime.combine(
        local_date,
        time(hour=hour, minute=minute),
        tzinfo=EDITORIAL_TIMEZONE,
    )


def process_articles(articles, *, editorial_time=None):
    """
    Run the complete AROUND THE MAIN v6 processing pipeline.

    When editorial_time is supplied, only information known by that
    Editorial Snapshot is processed. This keeps each edition tied to
    the information actually available at its publication boundary.
    """

    if not isinstance(articles, list):
        return []

    valid_articles = [
        article
        for article in articles
        if isinstance(article, dict)
        and article.get("title")
    ]

    if editorial_time is not None:
        valid_articles = filter_events_for_snapshot(
            [
                {"articles": [article]}
                for article in valid_articles
            ],
            editorial_time,
        )
        valid_articles = [
            event["articles"][0]
            for event in valid_articles
            if event.get("articles")
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

        facts = extract_facts({
            **result,
            "title": article.get("title", ""),
            "summary": article.get("summary", ""),
        })

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

        enriched["scale_numbers"] = facts.get(
            "scale_numbers",
            [],
        )

        normalized.append(enriched)

    if not normalized:
        return []

    clustered = cluster_articles(normalized)

    verified = verify_events(clustered)

    analyzed = analyze_events(verified)

    ranking_time = editorial_time

    if isinstance(ranking_time, str):
        text = ranking_time.strip()

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            ranking_time = datetime.fromisoformat(text)
        except ValueError:
            ranking_time = None

    ranked = rank_events(
        analyzed,
        now=ranking_time,
    )

    editorial = decide_events(ranked)

    content = build_contents(editorial)

    publication = build_publications(content)

    delivery = build_deliveries(publication)

    return delivery


def build_edition_from_articles(
    articles,
    publication_date=None,
    edition_time=None,
    *,
    event_memory=None,
    editorial_time=None,
    exclude_ignored=False,
):
    """
    Process articles and build a AROUND THE MAIN edition.

    The publication date and edition time define the Editorial
    Snapshot boundary. Information that became available after that
    boundary is excluded before normalization, clustering and ranking.
    """

    editorial_time = _build_editorial_time(
        publication_date,
        edition_time,
    )

    editorial = process_articles(
        articles,
        editorial_time=editorial_time,
    )

    edition = build_edition(
        editorial,
        publication_date=publication_date,
        edition_time=edition_time,
        exclude_ignored=exclude_ignored,
    )

    edition_id = edition.get("edition_id")

    if event_memory is not None and edition_id:
        for event in editorial:
            event_memory.remember(
                event,
                edition_id=edition_id,
            )

    return edition
