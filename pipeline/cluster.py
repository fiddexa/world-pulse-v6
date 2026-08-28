"""
WORLD PULSE v6 - Event Clustering

Conservative clustering of news articles into real-world events.
"""

from datetime import datetime, timezone
from typing import Any

from pipeline.extract import extract_facts
from pipeline.normalize import normalize_text


MAX_TIME_GAP_HOURS = 6.0
MIN_TEXT_SIMILARITY = 0.30


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def _article_text(article: dict) -> str:
    title = article.get("title", "")
    summary = article.get("summary", "")

    return normalize_text(
        f"{title} {summary}".strip()
    )


def _tokens(article: dict) -> set[str]:
    return {
        token
        for token in _article_text(article).split()
        if token
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0

    union = a | b

    if not union:
        return 0.0

    return len(a & b) / len(union)


def _time_compatible(a: dict, b: dict) -> bool:
    da = _parse_datetime(a.get("published_at"))
    db = _parse_datetime(b.get("published_at"))

    if da is None or db is None:
        return True

    gap_hours = abs((da - db).total_seconds()) / 3600.0

    return gap_hours <= MAX_TIME_GAP_HOURS


def _facts_compatible(a: dict, b: dict) -> bool:
    fa = extract_facts(a)
    fb = extract_facts(b)

    if not fa or not fb:
        return False

    types_a = set(fa.get("event_types", []))
    types_b = set(fb.get("event_types", []))

    if types_a and types_b and not (types_a & types_b):
        return False

    locations_a = set(fa.get("locations", []))
    locations_b = set(fb.get("locations", []))

    if locations_a and locations_b and not (locations_a & locations_b):
        return False

    actors_a = set(fa.get("actors", []))
    actors_b = set(fb.get("actors", []))

    if actors_a and actors_b and not (actors_a & actors_b):
        return False

    return True


def _similar_enough(a: dict, b: dict) -> bool:
    if not _time_compatible(a, b):
        return False

    if not _facts_compatible(a, b):
        return False

    fa = extract_facts(a)
    fb = extract_facts(b)

    types_a = set(fa.get("event_types", []))
    types_b = set(fb.get("event_types", []))

    locations_a = set(fa.get("locations", []))
    locations_b = set(fb.get("locations", []))

    actors_a = set(fa.get("actors", []))
    actors_b = set(fb.get("actors", []))

    objects_a = set(fa.get("objects", []))
    objects_b = set(fb.get("objects", []))

    shared_types = bool(types_a & types_b)
    shared_locations = bool(locations_a & locations_b)
    shared_actors = bool(actors_a & actors_b)
    shared_objects = bool(objects_a & objects_b)

    lexical = _jaccard(
        _tokens(a),
        _tokens(b),
    )

    # Strong event identity:
    # same event type + same location + reasonable wording overlap.
    #
    # This allows:
    # "Earthquake strikes Nepal"
    # "Major earthquake hits Nepal"
    #
    # to form one event even though the verbs differ.
    if shared_types and shared_locations:
        if lexical >= MIN_TEXT_SIMILARITY:
            return True

        if shared_actors:
            return True

        if shared_objects and lexical >= 0.20:
            return True

    # Same location + same actor + reasonable wording overlap.
    if (
        shared_locations
        and shared_actors
        and lexical >= 0.25
    ):
        return True

    return False


def _new_event(article: dict) -> dict:
    return {
        "articles": [article],
        "similarity_scores": [],
    }
def cluster_articles(articles: list[dict]) -> list[dict]:
    """
    Group news articles referring to the same real-world event.

    The function is intentionally conservative.
    """

    if not isinstance(articles, list):
        return []

    events: list[dict] = []

    for article in articles:
        if not isinstance(article, dict):
            continue

        title = article.get("title")

        if not title:
            continue

        placed = False

        for event in events:
            representative = event["articles"][0]

            if _similar_enough(article, representative):
                event["articles"].append(article)

                similarity = _jaccard(
                    _tokens(article),
                    _tokens(representative),
                )

                event["similarity_scores"].append(
                    round(similarity, 4)
                )

                placed = True
                break

        if not placed:
            events.append(
                _new_event(article)
            )

    return events
