"""
AROUND THE MAIN v6 - Editorial Decision Layer

Converts verification, intelligence, and ranking signals into a
conservative publication decision.

This layer does not rewrite facts and does not determine truth.
It decides how prominently an already-processed event should be
considered for publication.
"""

from typing import Any


IGNORE = "IGNORE"
STANDARD = "STANDARD"
IMPORTANT = "IMPORTANT"
TOP_STORY = "TOP_STORY"
FRONT_PAGE = "FRONT_PAGE"

LEAD_STORY = "LEAD_STORY"
SECTION_STORY = "SECTION_STORY"
BRIEF = "BRIEF"


def _safe_number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ranking(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("ranking")
    return value if isinstance(value, dict) else {}


def _verification(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("verification")
    return value if isinstance(value, dict) else {}


def _intelligence(event: Any) -> dict:
    if not isinstance(event, dict):
        return {}

    value = event.get("intelligence")
    return value if isinstance(value, dict) else {}


def _ranking_score(event: Any) -> float:
    if not isinstance(event, dict):
        return 0.0

    ranking = _ranking(event)

    value = ranking.get(
        "editorial_score",
        event.get("ranking_score", 0.0),
    )

    return max(
        0.0,
        min(100.0, _safe_number(value)),
    )


def _intelligence_score(event: Any) -> float:
    intelligence = _intelligence(event)

    return max(
        0.0,
        min(100.0, _safe_number(
            intelligence.get("score")
        )),
    )


def _verification_score(event: Any) -> float:
    verification = _verification(event)

    return max(
        0.0,
        min(100.0, _safe_number(
            verification.get("verification_score")
        )),
    )


def _verification_level(event: Any) -> str:
    return str(
        _verification(event).get(
            "verification_level",
            "UNCONFIRMED",
        )
    ).upper()


def _is_breaking(event: Any) -> bool:
    return bool(
        _ranking(event).get("breaking", False)
    )


def _article_count(event: Any) -> int:
    if not isinstance(event, dict):
        return 0

    articles = event.get("articles")

    if not isinstance(articles, list):
        return 0

    return sum(
        isinstance(article, dict)
        for article in articles
    )


def _maximum_casualty_number(event: Any) -> float:
    """
    Return the largest casualty figure available for the event.
    """

    if not isinstance(event, dict):
        return 0.0

    intelligence = _intelligence(event)

    value = intelligence.get(
        "maximum_casualty_number",
        0.0,
    )

    return max(
        0.0,
        _safe_number(value),
    )


def _is_major_humanitarian_event(event: Any) -> bool:
    """
    Identify exceptional events with direct large-scale
    human consequences.

    This is an editorial prominence signal, not a truth signal.
    """

    if not isinstance(event, dict):
        return False

    intelligence = _intelligence_score(event)
    casualties = _maximum_casualty_number(event)

    event_types = set()

    direct_types = event.get("event_types")

    if isinstance(direct_types, (list, tuple, set)):
        event_types.update(
            str(value).strip().lower()
            for value in direct_types
            if value
        )

    for article in event.get("articles", []):
        if not isinstance(article, dict):
            continue

        values = article.get("event_types")

        if isinstance(values, (list, tuple, set)):
            event_types.update(
                str(value).strip().lower()
                for value in values
                if value
            )

    direct_harm = {
        "casualty",
        "death",
        "attack",
        "military_conflict",
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
    }

    return (
        casualties >= 500
        and intelligence >= 70.0
        and bool(event_types & direct_harm)
    )


def editorial_decision(event: Any) -> str:
    """
    Return the recommended publication priority.

    This layer decides editorial treatment, not truth.
    """

    if not isinstance(event, dict):
        return IGNORE

    score = _ranking_score(event)
    intelligence = _intelligence_score(event)
    verification = _verification_score(event)
    verification_level = _verification_level(event)
    breaking = _is_breaking(event)
    article_count = _article_count(event)

    if score < 25.0:
        return IGNORE

    if (
        breaking
        and intelligence >= 65.0
        and verification_level != "UNCONFIRMED"
    ):
        return FRONT_PAGE


    if _is_major_humanitarian_event(event):
        return FRONT_PAGE
    if (
        score >= 85.0
        and verification_level in {
            "MULTI_SOURCE",
            "WIDELY_CONFIRMED",
        }
    ):
        return FRONT_PAGE

    if (
        score >= 70.0
        and verification_level != "UNCONFIRMED"
    ):
        return TOP_STORY

    if score >= 55.0:
        return IMPORTANT

    if score >= 40.0:
        return STANDARD

    if (
        intelligence >= 50.0
        and article_count >= 1
        and verification >= 20.0
    ):
        return STANDARD

    return IGNORE


def editorial_role(
    event: Any,
    decision: str | None = None,
) -> str:
    """
    Map a publication decision to an edition role.
    """

    if decision is None:
        decision = editorial_decision(event)

    if decision == FRONT_PAGE:
        return LEAD_STORY

    if decision in {
        TOP_STORY,
        IMPORTANT,
    }:
        return SECTION_STORY

    return BRIEF


def decide_event(event: Any) -> dict:
    """
    Return stable editorial metadata without modifying
    the original event.
    """

    if not isinstance(event, dict):
        return {
            "decision": IGNORE,
            "role": BRIEF,
            "ranking_score": 0.0,
            "intelligence_score": 0.0,
            "verification_score": 0.0,
            "verification_level": "UNCONFIRMED",
            "breaking": False,
        }

    decision = editorial_decision(event)

    return {
        "decision": decision,
        "role": editorial_role(
            event,
            decision,
        ),
        "ranking_score": round(
            _ranking_score(event),
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
        "verification_level": _verification_level(event),
        "breaking": _is_breaking(event),
    }


def decide_events(events: Any) -> list[dict]:
    """
    Add editorial metadata to events without
    modifying the original events.
    """

    if not isinstance(events, list):
        return []

    results = []

    for event in events:
        if not isinstance(event, dict):
            continue

        result = dict(event)
        result["editorial"] = decide_event(event)

        results.append(result)

    return results
