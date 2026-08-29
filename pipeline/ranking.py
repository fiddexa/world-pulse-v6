"""
WORLD PULSE v6 - Editorial Ranking Layer

Ranks clustered events for editorial placement.

Ranking is deliberately separate from:
- extraction
- clustering
- verification
- objective intelligence

The score estimates editorial priority, not truth.
"""

from datetime import datetime, timezone
from typing import Any


def _safe_number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _articles(event: Any) -> list[dict]:
    if not isinstance(event, dict):
        return []

    value = event.get("articles")

    if not isinstance(value, list):
        return []

    return [
        article
        for article in value
        if isinstance(article, dict)
    ]


def _published_dates(event: dict) -> list[datetime]:
    dates = []

    for article in _articles(event):
        value = article.get("published_at")

        if not value:
            continue

        if isinstance(value, datetime):
            dt = value
        else:
            text = str(value).strip()

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"

            try:
                dt = datetime.fromisoformat(text)
            except ValueError:
                continue

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        dates.append(dt)

    return dates


def freshness_score(event: dict, now: datetime | None = None) -> float:
    """
    Score how recent the event is.

    0-100.
    Unknown publication time receives a neutral score.
    """

    dates = _published_dates(event)

    if not dates:
        return 50.0

    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    latest = max(dates)

    age_hours = max(
        0.0,
        (now - latest).total_seconds() / 3600.0,
    )

    if age_hours <= 1:
        return 100.0

    if age_hours <= 3:
        return 90.0

    if age_hours <= 6:
        return 80.0

    if age_hours <= 12:
        return 65.0

    if age_hours <= 24:
        return 50.0

    if age_hours <= 48:
        return 30.0

    return 10.0


def _verification_score(event: dict) -> float:
    verification = event.get("verification")

    if not isinstance(verification, dict):
        return 0.0

    return max(
        0.0,
        min(
            100.0,
            _safe_number(
                verification.get("verification_score")
            ),
        ),
    )


def _intelligence_score(event: dict) -> float:
    intelligence = event.get("intelligence")

    if not isinstance(intelligence, dict):
        return 0.0

    return max(
        0.0,
        min(
            100.0,
            _safe_number(
                intelligence.get("score")
            ),
        ),
    )


def _article_count(event: dict) -> int:
    return len(_articles(event))


def _scope_score(event: dict) -> float:
    """
    Supporting editorial signal based on reporting breadth.
    """

    count = _article_count(event)

    if count <= 1:
        return 20.0

    if count == 2:
        return 45.0

    if count == 3:
        return 65.0

    if count <= 5:
        return 80.0

    return 90.0


def editorial_score(
    event: Any,
    now: datetime | None = None,
) -> float:
    """
    Calculate editorial priority from 0 to 100.

    This is NOT a truth score.

    Weighting:
        intelligence  45%
        verification  20%
        freshness     20%
        reporting     15%
    """

    if not isinstance(event, dict):
        return 0.0

    intelligence = _intelligence_score(event)
    verification = _verification_score(event)
    freshness = freshness_score(event, now)
    scope = _scope_score(event)

    score = (
        intelligence * 0.45
        + verification * 0.20
        + freshness * 0.20
        + scope * 0.15
    )

    return round(
        max(0.0, min(100.0, score)),
        2,
    )
def editorial_level(score: Any) -> str:
    value = _safe_number(score)

    if value >= 85:
        return "FRONT_PAGE"
    if value >= 70:
        return "TOP_STORY"
    if value >= 55:
        return "IMPORTANT"
    if value >= 40:
        return "STANDARD"

    return "LOW_PRIORITY"


def is_breaking(event: Any, now: datetime | None = None) -> bool:
    """
    Breaking means very recent + sufficiently important.

    Verification is intentionally not required here:
    a major event may initially have only one source.
    """

    if not isinstance(event, dict):
        return False

    intelligence = _intelligence_score(event)
    freshness = freshness_score(event, now)

    return (
        intelligence >= 65.0
        and freshness >= 90.0
    )


def rank_event(
    event: Any,
    now: datetime | None = None,
) -> dict:
    """
    Add editorial ranking metadata without modifying the original event.
    """

    if not isinstance(event, dict):
        return {}

    score = editorial_score(event, now)

    result = dict(event)

    result["ranking_score"] = score
    result["ranking_significance"] = editorial_level(score)

    result["ranking"] = {
        "editorial_score": score,
        "editorial_level": editorial_level(score),
        "freshness_score": round(
            freshness_score(event, now),
            2,
        ),
        "intelligence_score": round(
            _intelligence_score(event),
            2,
        ),
        "verification_score": round(
            _verification_score(event),
            2,
        ),
        "scope_score": round(
            _scope_score(event),
            2,
        ),
        "breaking": is_breaking(event, now),
    }

    return result


def rank_events(
    events: Any,
    now: datetime | None = None,
) -> list[dict]:
    """
    Rank events from highest to lowest editorial priority.

    Original event order is used as the deterministic tie-breaker.
    """

    if not isinstance(events, list):
        return []

    ranked = []

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue

        result = rank_event(event, now)

        score = result.get("ranking", {}).get(
            "editorial_score",
            0.0,
        )

        ranked.append(
            (
                -_safe_number(score),
                index,
                result,
            )
        )

    ranked.sort(key=lambda item: (item[0], item[1]))

    return [
        result
        for _, _, result in ranked
    ]
