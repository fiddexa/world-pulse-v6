import re
"""
AROUND THE MAIN v6 - Event Clustering

Conservative clustering of news articles into real-world events.
"""

from datetime import datetime, timezone
from typing import Any

from pipeline.extract import extract_facts
from pipeline.normalize import normalize_text


MAX_TIME_GAP_HOURS = 6.0
MIN_TEXT_SIMILARITY = 0.30

# Broad labels are useful for categorisation but are too weak
# to establish the identity of a real-world event.
SPECIFIC_EVENT_TYPES = {
    "attack",
    "missile_strike",
    "airstrike",
    "drone_attack",
    "bombing",
    "explosion",
    "earthquake",
    "tsunami",
    "volcano",
    "hurricane",
    "flood",
    "wildfire",
    "disease",
    "death",
}

TITLE_ANCHOR_STOPWORDS = {
    "the",
    "and",
    "after",
    "before",
    "amid",
    "says",
    "said",
    "says",
    "urges",
    "warns",
    "calls",
    "live",
    "watch",
    "new",
    "latest",
    "world",
    "global",
    "europe",
    "european",
    "international",
    "government",
    "president",
    "minister",
    "leaders",
    "leader",
    "official",
    "officials",
    "report",
    "reports",
    "news",
    "today",
    "not",
    "alone",
    "darkness",
    "single",
    "biggest",
    "largest",
    "major",
    "power",
    "final",
    "temporary",
    "first",
    "second",
    "three",
    "two",
    "one",
    "must",
    "may",
    "could",
    "would",
    "will",
}

LOCATION_IDENTITY_ALIASES = {
    "moldovan": "moldova",
    "norwegian": "norway",
    "finland": "finland",
    "finnish": "finland",
    "gambia": "gambia",
    "gambian": "gambia",
    "cambodia": "cambodia",
    "cambodian": "cambodia",
    "qatar": "qatar",
    "qatari": "qatar",
    "libya": "libya",
    "libyan": "libya",
    "gambia": "gambia",
    "gambian": "gambia",
    "argentina": "argentina",
    "argentine": "argentina",
    "spain": "spain",
    "spanish": "spain",
    "moldova": "moldova",
    "norway": "norway",
}


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


def _title_tokens(article: dict) -> set[str]:
    title = normalize_text(
        article.get("title", "")
    )

    return {
        token
        for token in title.split()
        if token
    }


def _tokens(article: dict) -> set[str]:
    return {
        token
        for token in _article_text(article).split()
        if token
    }


def _title_similarity(a: dict, b: dict) -> float:
    return _jaccard(
        _title_tokens(a),
        _title_tokens(b),
    )


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0

    union = a | b

    if not union:
        return 0.0

    return len(a & b) / len(union)


def _time_gap_hours(a: dict, b: dict) -> float | None:
    da = _parse_datetime(a.get("published_at"))
    db = _parse_datetime(b.get("published_at"))

    if da is None or db is None:
        return None

    return abs(
        (da - db).total_seconds()
    ) / 3600.0


def _time_compatible(a: dict, b: dict) -> bool:
    gap_hours = _time_gap_hours(a, b)

    if gap_hours is None:
        return True

    return gap_hours <= 24.0


def _identity_facts(article: dict) -> dict:
    """
    Extract event-identity facts from the headline.

    Location aliases are resolved directly here rather than
    depending on the global extractor vocabulary. This allows
    demonyms such as "Finnish" or "Gambian" to resolve to their
    canonical geographic identities.
    """

    if not isinstance(article, dict):
        return {}

    title = str(
        article.get("title") or ""
    ).strip()

    if not title:
        return {}

    identity_title = re.sub(
        r"([A-Za-z]+)[\\'’]s\\b",
        r"\\1",
        title,
    )

    lowered = identity_title.lower()

    facts = extract_facts(
        {
            "title": identity_title,
            "summary": "",
        }
    )

    locations = set(
        facts.get("locations", [])
    )

    for alias, canonical in LOCATION_IDENTITY_ALIASES.items():
        if re.search(
            rf"\\b{re.escape(alias)}\\b",
            lowered,
        ):
            locations.add(canonical)

    facts["locations"] = sorted(locations)

    return facts


def _title_anchor_tokens(article: dict) -> set[str]:
    """
    Extract high-signal entity anchors from the headline.

    Geographic demonyms are canonicalized so that variants such
    as "Gambian" / "Gambia" and "Finnish" / "Finland" resolve
    to the same identity.
    """

    if not isinstance(article, dict):
        return set()

    title = str(
        article.get("title") or ""
    ).strip()

    if not title:
        return set()

    anchors = set()

    for raw in re.findall(
        r"[A-Za-z][A-Za-z0-9&.-]*",
        title,
    ):
        token = raw.strip(
            ".,:;!?()[]{}\\\"'"
        )

        if not token:
            continue

        normalized = token.lower()

        if normalized in TITLE_ANCHOR_STOPWORDS:
            continue

        canonical = LOCATION_IDENTITY_ALIASES.get(
            normalized
        )

        if canonical:
            anchors.add(canonical)
            continue

        # Preserve all-uppercase abbreviations.
        if token.isupper() and len(token) >= 2:
            anchors.add(normalized)
            continue

        # Capitalized named entities / organizations.
        if token[0].isupper() and len(token) >= 3:
            anchors.add(normalized)

    return anchors

def _facts_compatible(a: dict, b: dict) -> bool:
    fa = _identity_facts(a)
    fb = _identity_facts(b)

    if not fa or not fb:
        return False

    types_a = set(fa.get("event_types", []))
    types_b = set(fb.get("event_types", []))

    specific_a = types_a & SPECIFIC_EVENT_TYPES
    specific_b = types_b & SPECIFIC_EVENT_TYPES

    # Different specific event types are a meaningful conflict.
    if specific_a and specific_b and not (specific_a & specific_b):
        return False

    locations_a = set(fa.get("locations", []))
    locations_b = set(fb.get("locations", []))

    if locations_a and locations_b and not (locations_a & locations_b):
        return False

    actors_a = set(fa.get("actors", []))
    actors_b = set(fa.get("actors", []))

    if actors_a and actors_b and not (actors_a & actors_b):
        return False

    return True


def _similar_enough(a: dict, b: dict) -> bool:
    if not _time_compatible(a, b):
        return False

    if not _facts_compatible(a, b):
        return False

    fa = _identity_facts(a)
    fb = _identity_facts(b)

    types_a = set(fa.get("event_types", []))
    types_b = set(fb.get("event_types", []))

    locations_a = set(fa.get("locations", []))
    locations_b = set(fb.get("locations", []))

    actors_a = set(fa.get("actors", []))
    actors_b = set(fb.get("actors", []))

    specific_a = types_a & SPECIFIC_EVENT_TYPES
    specific_b = types_b & SPECIFIC_EVENT_TYPES

    shared_locations = bool(
        locations_a & locations_b
    )

    shared_actors = bool(
        actors_a & actors_b
    )

    shared_specific_types = bool(
        specific_a & specific_b
    )

    shared_anchors = (
        _title_anchor_tokens(a)
        & _title_anchor_tokens(b)
    )

    title_lexical = _title_similarity(a, b)

    lexical = _jaccard(
        _tokens(a),
        _tokens(b),
    )

    gap_hours = _time_gap_hours(a, b)

    # Very strong headline match. Allow the wider 24-hour
    # editorial window because the titles themselves strongly
    # establish the same event.
    if title_lexical >= 0.40:
        return True

    # Normal window: up to 6 hours.
    if gap_hours is None or gap_hours <= MAX_TIME_GAP_HOURS:
        if (
            shared_anchors
            and lexical >= 0.18
        ):
            return True

        if (
            shared_locations
            and title_lexical >= 0.18
            and lexical >= 0.15
        ):
            return True

        if (
            shared_locations
            and shared_actors
            and lexical >= 0.12
        ):
            return True

        if (
            shared_specific_types
            and (
                shared_locations
                or shared_actors
            )
            and title_lexical >= 0.18
            and lexical >= 0.15
        ):
            return True

    # Extended window: 6–24 hours. We require stronger evidence
    # than normal-time matches.
    if gap_hours is not None and gap_hours <= 24.0:
        if (
            shared_anchors
            and lexical >= 0.20
        ):
            return True

        if (
            shared_locations
            and (
                shared_actors
                or shared_specific_types
            )
            and title_lexical >= 0.20
            and lexical >= 0.18
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
            grouped_articles = event.get(
                "articles",
                [],
            )

            if not isinstance(
                grouped_articles,
                list,
            ):
                continue

            matched_article = None

            for existing in grouped_articles:
                if _similar_enough(
                    article,
                    existing,
                ):
                    matched_article = existing
                    break

            if matched_article is not None:
                event["articles"].append(article)

                similarity = _jaccard(
                    _tokens(article),
                    _tokens(matched_article),
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
