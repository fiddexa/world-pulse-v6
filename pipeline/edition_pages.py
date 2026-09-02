"""
AROUND THE MAIN — Edition Page Manager

Builds the logical page structure of one newspaper edition.

Responsibilities:
- PAGE 01 is always the front page;
- additional pages are created only when there is real content;
- no editorial rewriting;
- no ranking;
- no image downloading;
- no external publication.

This module describes WHAT belongs on each page.
The newspaper renderer decides HOW each page looks.
"""

from dataclasses import dataclass, field
from typing import Any


# =====================================================================
# PAGE TYPES
# =====================================================================

PAGE_FRONT = "FRONT_PAGE"
PAGE_WORLD = "WORLD"
PAGE_BUSINESS = "BUSINESS"
PAGE_TECHNOLOGY = "TECHNOLOGY"
PAGE_ECONOMY = "ECONOMY"
PAGE_SCIENCE = "SCIENCE"
PAGE_HEALTH = "HEALTH"
PAGE_SPORTS = "SPORTS"


@dataclass
class EditionPage:
    """
    One logical newspaper page.
    """

    page_number: int
    page_type: str
    title: str
    events: list[dict[str, Any]] = field(
        default_factory=list
    )

    @property
    def page_label(self) -> str:
        return f"PAGE {self.page_number:02d}"

    @property
    def is_empty(self) -> bool:
        return len(self.events) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "page_label": self.page_label,
            "page_type": self.page_type,
            "title": self.title,
            "events": self.events,
        }


# =====================================================================
# HELPERS
# =====================================================================

def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return []


def _event_category(event: dict[str, Any]) -> str:
    """
    Read category without changing the event.

    Different pipeline stages may store the category
    under slightly different keys.
    """

    for key in (
        "category",
        "section",
        "topic",
    ):
        value = event.get(key)

        if value:
            return str(value).strip().lower()

    content = event.get("content")

    if isinstance(content, dict):
        for key in (
            "category",
            "section",
            "topic",
        ):
            value = content.get(key)

            if value:
                return str(value).strip().lower()

    return ""


def _category_page_type(category: str) -> str | None:
    category = category.lower().strip()

    mapping = {
        "world": PAGE_WORLD,
        "geopolitics": PAGE_WORLD,
        "business": PAGE_BUSINESS,
        "technology": PAGE_TECHNOLOGY,
        "tech": PAGE_TECHNOLOGY,
        "economy": PAGE_ECONOMY,
        "science": PAGE_SCIENCE,
        "health": PAGE_HEALTH,
        "sports": PAGE_SPORTS,
        "sport": PAGE_SPORTS,
    }

    return mapping.get(category)


def _page_title(page_type: str) -> str:
    titles = {
        PAGE_FRONT: "FRONT PAGE",
        PAGE_WORLD: "WORLD",
        PAGE_BUSINESS: "BUSINESS",
        PAGE_TECHNOLOGY: "TECHNOLOGY",
        PAGE_ECONOMY: "ECONOMY",
        PAGE_SCIENCE: "SCIENCE",
        PAGE_HEALTH: "HEALTH",
        PAGE_SPORTS: "SPORTS",
    }

    return titles.get(
        page_type,
        page_type,
    )


# =====================================================================
# PAGE BUILDER
# =====================================================================


def build_edition_pages(
    edition: dict[str, Any],
) -> list[EditionPage]:
    """
    Build physical newspaper pages for one edition.

    PAGE 01 is the front page.

    Remaining stories are packed into dense physical pages instead
    of creating one sparse page per category.

    Rules:
    - no empty pages;
    - no duplicate front-page events;
    - preserve editorial order;
    - preserve category information;
    - small category groups may share a page stream;
    - physical pagination is decided by the renderer from measured content;
    - page title reflects categories actually present.
    """

    if not isinstance(edition, dict):
        raise ValueError("edition must be a dictionary")

    pages: list[EditionPage] = []

    # ================================================================
    # PAGE 01
    # ================================================================

    front_events: list[dict[str, Any]] = []

    top_story = edition.get("top_story")

    if isinstance(top_story, dict):
        front_events.append(top_story)

    for key in ("main_stories", "briefs"):
        values = edition.get(key, [])

        if not isinstance(values, list):
            continue

        for event in values:
            if isinstance(event, dict):
                front_events.append(event)

    unique_front = []
    seen = set()

    for event in front_events:
        marker = id(event)

        if marker in seen:
            continue

        seen.add(marker)
        unique_front.append(event)

    front_events = unique_front

    pages.append(
        EditionPage(
            page_number=1,
            page_type=PAGE_FRONT,
            title=_page_title(PAGE_FRONT),
            events=front_events,
        )
    )

    # ================================================================
    # REMAINING EVENTS
    # ================================================================

    remaining: list[dict[str, Any]] = []

    front_ids = {
        id(event)
        for event in front_events
    }

    for key in (
        "additional_events",
        "remaining_events",
        "overflow_events",
    ):
        values = edition.get(key, [])

        if not isinstance(values, list):
            continue

        for event in values:
            if not isinstance(event, dict):
                continue

            if id(event) in front_ids:
                continue

            remaining.append(event)

    if not remaining:
        return pages

    # ================================================================
    # GROUP INTO CATEGORY STREAMS
    # ================================================================

    category_order = [
        PAGE_WORLD,
        PAGE_BUSINESS,
        PAGE_TECHNOLOGY,
        PAGE_ECONOMY,
        PAGE_SCIENCE,
        PAGE_HEALTH,
        PAGE_SPORTS,
    ]

    groups: dict[str, list[dict[str, Any]]] = {}

    for event in remaining:
        category = _event_category(event)
        page_type = _category_page_type(category)

        if page_type is None:
            page_type = PAGE_WORLD

        groups.setdefault(page_type, []).append(event)

    # ================================================================
    # DENSE PAGE PACKING
    # ================================================================

    page_number = 2
    current_events: list[dict[str, Any]] = []
    current_types: list[str] = []

    def flush_page():
        nonlocal page_number
        nonlocal current_events
        nonlocal current_types

        if not current_events:
            return

        unique_types = []

        for item in current_types:
            if item not in unique_types:
                unique_types.append(item)

        if len(unique_types) == 1:
            page_type = unique_types[0]
            title = _page_title(page_type)
        else:
            page_type = "MIXED"
            # Physical pages can carry several editorial streams.  Their
            # individual categories remain visible on every story card, so a
            # long slash-separated heading only adds visual noise.
            title = "GLOBAL NEWS"

        pages.append(
            EditionPage(
                page_number=page_number,
                page_type=page_type,
                title=title,
                events=list(current_events),
            )
        )

        page_number += 1
        current_events = []
        current_types = []

    for page_type in category_order:
        events = groups.get(page_type, [])

        for event in events:
            current_events.append(event)
            current_types.append(page_type)

    flush_page()

    return pages
