"""
WORLD PULSE v6 - Production Delivery

Explicit production entry point for publishing an already-built
WORLD PULSE edition.

This layer does not schedule, collect news, or rebuild an edition.
It only connects an existing edition to edition-level publication
and Telegram delivery.
"""

from typing import Any

from pipeline.edition_production import publish_edition


def deliver_production_edition(
    edition: Any,
    *,
    log=None,
    publisher=None,
) -> dict:
    """
    Publish one already-built production edition.

    The edition itself is never modified.
    """
    if not isinstance(edition, dict):
        return {
            "status": "FAILED",
            "reason": "INVALID_EDITION",
        }

    result = publish_edition(
        edition,
        log=log,
        publisher=publisher,
    )

    return {
        "edition_id": edition.get("edition_id"),
        "status": result.get("status", "FAILED"),
        "delivery": result.get("delivery"),
        "publication": result.get("publication"),
    }
