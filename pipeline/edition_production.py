"""
AROUND THE MAIN v6 - Edition Production Orchestrator

Connects an already-built production edition to the
edition-level publication and Telegram delivery layers.

This module does not collect news and does not schedule runs.

It is intentionally separate from the existing event-level
delivery system and from the production scheduler.
"""

from typing import Any

from pipeline.edition_approval import (
    APPROVAL_APPROVED,
    get_edition_approval_status,
)
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
    approval_manifest_path=None,
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

    edition_id = str(edition.get("edition_id") or "").strip()
    approval_status = get_edition_approval_status(
        edition_id,
        approval_manifest_path,
    )

    if approval_status != APPROVAL_APPROVED:
        return {
            "status": FAILED,
            "reason": "APPROVAL_NOT_APPROVED",
            "edition_id": edition_id,
            "approval_status": approval_status,
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
        approval_manifest_path=approval_manifest_path,
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
