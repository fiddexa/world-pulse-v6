"""
AROUND THE MAIN v6 - Edition Production Orchestrator

Connects an already-built production edition to the
edition-level publication and Telegram delivery layers.

This module does not collect news and does not schedule runs.

It is intentionally separate from the existing event-level
delivery system and from the production scheduler.
"""

from typing import Any

from pipeline.edition_publication import build_edition_publication
from pipeline.edition_telegram_runner import (
    publish_edition_to_telegram,
)


COMPLETED = "COMPLETED"
FAILED = "FAILED"


def publish_edition(
    edition: Any,
    *,
    log=None,
    publisher=None,
) -> dict:
    """
    Build and publish one AROUND THE MAIN edition.

    Returns both the publication package and delivery result.

    The original edition is never modified.
    """
    if not isinstance(edition, dict):
        return {
            "status": FAILED,
            "reason": "INVALID_EDITION",
        }

    publication = build_edition_publication(
        edition
    )

    if not publication:
        return {
            "status": FAILED,
            "reason": "INVALID_PUBLICATION",
        }

    delivery = publish_edition_to_telegram(
        publication,
        log=log,
        publisher=publisher,
    )

    return {
        "status": (
            COMPLETED
            if delivery.get("status") == "SENT"
            else delivery.get("status", FAILED)
        ),
        "edition_id": publication.get("edition_id"),
        "publication": publication,
        "delivery": delivery,
    }
