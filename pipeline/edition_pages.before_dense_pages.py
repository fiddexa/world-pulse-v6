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
    Build the logical pages for one edition.

    Rules:

    1. PAGE 01 is always FRONT PAGE.
    2. Only events that actually exist are used.
    3. Empty category pages are never created.
    4. Events already placed on PAGE 01 are not duplicated.
    5. Remaining events are grouped by category.
    6. Category order is deterministic.
    """

    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    pages: list[EditionPage] = []

    # ================================================================
    # PAGE 01 — FRONT PAGE
    # ================================================================

    front_events: list[dict[str, Any]] = []

    top_story = edition.get(
        "top_story"
    )

    if isinstance(top_story, dict):
        front_events.append(top_story)

    for event in _as_list(
        edition.get("main_stories")
    ):
        if isinstance(event, dict):
            front_events.append(event)

    for event in _as_list(
        edition.get("briefs")
    ):
        if isinstance(event, dict):
            front_events.append(event)

    # Remove duplicate object/event references while preserving order.
    unique_front = []
    seen_ids = set()

    for event in front_events:
        marker = id(event)

        if marker in seen_ids:
            continue

        seen_ids.add(marker)
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
    # REMAINING CONTENT
    # ================================================================

    # At the current production stage all published events are already
    # represented on PAGE 01. We nevertheless keep this logic ready
    # for future multi-page editions where an explicit `additional_events`
    # collection may be supplied.

    additional_events = []

    for key in (
        "additional_events",
        "remaining_events",
        "overflow_events",
    ):
        for event in _as_list(
            edition.get(key)
        ):
            if isinstance(event, dict):
                additional_events.append(event)

    if not additional_events:
        return pages

    # Prevent an event already present on PAGE 01 from being repeated.
    front_markers = {
        id(event)
        for event in front_events
    }

    additional_events = [
        event
        for event in additional_events
        if id(event) not in front_markers
    ]

    if not additional_events:
        return pages

    # ================================================================
    # GROUP BY CATEGORY
    # ================================================================

    groups: dict[str, list[dict[str, Any]]] = {}

    for event in additional_events:
        category = _event_category(event)

        page_type = _category_page_type(
            category
        )

        if page_type is None:
            # Unknown categories are kept in a general WORLD section
            # rather than silently discarded.
            page_type = PAGE_WORLD

        groups.setdefault(
            page_type,
            [],
        ).append(event)

    # Deterministic newspaper order.
    page_order = [
        PAGE_WORLD,
        PAGE_BUSINESS,
        PAGE_TECHNOLOGY,
        PAGE_ECONOMY,
        PAGE_SCIENCE,
        PAGE_HEALTH,
        PAGE_SPORTS,
    ]

    page_number = 2

    for page_type in page_order:
        events = groups.get(
            page_type,
            [],
        )

        if not events:
            continue

        pages.append(
            EditionPage(
                page_number=page_number,
                page_type=page_type,
                title=_page_title(page_type),
                events=events,
            )
        )

        page_number += 1

    return pages


# =====================================================================
# PUBLICATION METADATA
# =====================================================================

def build_page_manifest(
    edition: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a serializable manifest for the complete edition.
    """

    pages = build_edition_pages(
        edition
    )

    edition_id = edition.get(
        "edition_id"
    )

    return {
        "edition_id": edition_id,
        "page_count": len(pages),
        "pages": [
            page.to_dict()
            for page in pages
        ],
    }
