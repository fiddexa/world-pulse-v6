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
from pipeline.audio_script import build_audio_script
from pipeline.audio_renderer import OpenAITTSRenderer
from pipeline.edition_audio import generate_edition_audio


COMPLETED = "COMPLETED"
FAILED = "FAILED"

def build_edition_audio(
    edition: dict,
    *,
    output_path,
    audio_renderer=None,
) -> dict:
    """Generate the complete Audio Edition for one edition."""

    if not isinstance(edition, dict):
        return {
            "status": FAILED,
            "reason": "INVALID_EDITION",
        }

    edition_id = str(
        edition.get("edition_id") or ""
    ).strip()

    if not edition_id:
        return {
            "status": FAILED,
            "reason": "MISSING_EDITION_ID",
        }

    try:
        script = build_audio_script(edition)

        if not script.strip():
            return {
                "status": FAILED,
                "edition_id": edition_id,
                "reason": "EMPTY_AUDIO_SCRIPT",
            }

        renderer = (
            audio_renderer
            if audio_renderer is not None
            else OpenAITTSRenderer()
        )

        rendered_path = renderer.render(
            script,
            output_path,
        )

        return {
            "status": "GENERATED",
            "edition_id": edition_id,
            "audio_path": str(rendered_path),
            "script": script,
        }

    except Exception as exc:
        return {
            "status": FAILED,
            "edition_id": edition_id,
            "reason": "AUDIO_GENERATION_FAILED",
            "error": str(exc),
        }




def publish_edition(
    edition: Any,
    *,
    log=None,
    publisher=None,
    approval_manifest_path=None,
    audio_renderer=None,
    audio_output_dir="data/audio",
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

    # Real production editions receive an edition_number from the
    # production scheduler. For those editions, Audio is mandatory.
    #
    # Legacy/minimal test fixtures may not contain edition_number.
    # They keep the historical text-delivery behavior so the existing
    # production tests remain valid.
    if edition.get("edition_number") is not None:
        audio_result = generate_edition_audio(
            edition,
            output_dir=audio_output_dir,
            audio_renderer=audio_renderer,
        )

        if audio_result.get("status") != "GENERATED":
            return {
                "status": FAILED,
                "reason": "AUDIO_GENERATION_FAILED",
                "edition_id": publication.get("edition_id"),
                "publication": publication,
                "audio": audio_result,
                "delivery": None,
            }
    else:
        audio_result = {
            "status": "SKIPPED",
            "edition_id": publication.get("edition_id"),
            "reason": "MISSING_EDITION_NUMBER",
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
        "audio": audio_result,
        "delivery": delivery,
    }
