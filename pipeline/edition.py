"""
WORLD PULSE v6 - Edition Builder

Builds a deterministic editorial edition from processed events.

This layer does not generate or rewrite news.
It only decides how already-processed events should be
organized into an edition.
"""

from typing import Any


SECTION_ORDER = (
    "world",
    "geopolitics",
    "business",
    "energy",
    "technology",
    "science_health",
    "climate",
    "trade_logistics",
    "society",
    "culture",
    "sports",
)


ROLE_ORDER = (
    "TOP_STORY",
    "MAIN_STORY",
    "BRIEF",
)


def _safe_number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _editorial(event: dict) -> dict:
    value = event.get("editorial")

    if isinstance(value, dict):
        return value

    return {}


def _score(event: dict) -> float:
    editorial = _editorial(event)

    return _safe_number(
        editorial.get(
            "ranking_score",
            event.get("ranking_score", 0.0),
        )
    )


def _role(event: dict) -> str:
    editorial = _editorial(event)

    role = editorial.get("role")

    if role:
        return str(role).strip().upper()

    return "BRIEF"


def _section(event: dict) -> str:
    """
    Determine the primary edition section.

    Existing event/category information is preferred.
    Unknown categories fall back to 'world'.
    """

    category = event.get("category")

    if category:
        value = str(category).strip().lower()

        aliases = {
            "world": "world",
            "international": "world",
            "politics": "geopolitics",
            "political": "geopolitics",
            "geopolitics": "geopolitics",
            "security": "geopolitics",
            "business": "business",
            "finance": "business",
            "economy": "business",
            "economic": "business",
            "energy": "energy",
            "oil": "energy",
            "gas": "energy",
            "technology": "technology",
            "tech": "technology",
            "ai": "technology",
            "science": "science_health",
            "health": "science_health",
            "medical": "science_health",
            "climate": "climate",
            "environment": "climate",
            "trade": "trade_logistics",
            "logistics": "trade_logistics",
            "society": "society",
            "culture": "culture",
            "sports": "sports",
            "sport": "sports",
        }

        return aliases.get(value, "world")

    return "world"


def _is_publishable(event: dict) -> bool:
    if not isinstance(event, dict):
        return False

    editorial = _editorial(event)

    decision = str(
        editorial.get("decision", "STANDARD")
    ).strip().upper()

    return decision not in {
        "REJECT",
        "EXCLUDE",
        "HOLD",
    }


def _sort_key(event: dict) -> tuple:
    role = _role(event)

    try:
        role_index = ROLE_ORDER.index(role)
    except ValueError:
        role_index = len(ROLE_ORDER)

    return (
        role_index,
        -_score(event),
    )


def build_edition(events: Any) -> dict:
    """
    Build one deterministic edition structure.

    No external services, AI APIs, or network calls are used.
    """

    if not isinstance(events, list):
        events = []

    publishable = [
        event
        for event in events
        if isinstance(event, dict)
        and _is_publishable(event)
    ]

    ordered = sorted(
        publishable,
        key=_sort_key,
    )

    top_story = None
    main_stories = []
    briefs = []

    for event in ordered:
        role = _role(event)

        if role == "TOP_STORY" and top_story is None:
            top_story = event
        elif role == "MAIN_STORY":
            main_stories.append(event)
        else:
            briefs.append(event)

    sections = {
        section: []
        for section in SECTION_ORDER
    }

    for event in ordered:
        section = _section(event)

        sections.setdefault(
            section,
            [],
        ).append(event)

    return {
        "edition_type": "WORLD_PULSE",
        "event_count": len(ordered),
        "top_story": top_story,
        "main_stories": main_stories,
        "briefs": briefs,
        "sections": sections,
    }


def build_editions(events: Any) -> list[dict]:
    """
    Convenience wrapper for future multi-edition support.
    """

    return [build_edition(events)]
