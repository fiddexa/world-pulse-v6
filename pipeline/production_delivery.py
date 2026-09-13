"""
AROUND THE MAIN v6 - Production Delivery

Explicit production entry point for publishing an already-built
AROUND THE MAIN edition.

This layer does not schedule, collect news, or rebuild an edition.
It connects an approved edition to newspaper-image and audio delivery.
The reusable text publication package is still returned for other channels.
"""

from typing import Any

from pipeline.edition_production import publish_edition


def deliver_production_edition(
    edition: Any,
    *,
    log=None,
    publisher=None,
    newspaper_publisher=None,
    approval_manifest_path=None,
    newspaper_output_root="data/newspaper",
    audio_renderer=None,
    audio_output_dir="data/audio",
    audio_publisher=None,
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
        newspaper_publisher=newspaper_publisher,
        approval_manifest_path=approval_manifest_path,
        newspaper_output_root=newspaper_output_root,
        audio_renderer=audio_renderer,
        audio_output_dir=audio_output_dir,
        audio_publisher=audio_publisher,
    )

    return {
        "edition_id": edition.get("edition_id"),
        "status": result.get("status", "FAILED"),
        "delivery": result.get("newspaper_delivery"),
        "newspaper": result.get("newspaper"),
        "audio": result.get("audio"),
        "audio_delivery": result.get("audio_delivery"),
        "publication": result.get("publication"),
    }
