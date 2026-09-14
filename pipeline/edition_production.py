"""
AROUND THE MAIN v6 - Edition Production Orchestrator

Connects an already-built production edition to the
edition-level newspaper image and audio delivery layers.

The text publication package is still built and retained for
other social channels and downstream integrations, but production
Telegram delivery uses rendered newspaper PNG pages, not text.
"""

from pathlib import Path
from typing import Any
import re

from pipeline.edition_approval import (
    APPROVAL_APPROVED,
    get_edition_approval_status,
)
from pipeline.edition_publication import build_edition_publication
from pipeline.edition_rendering import render_edition
from pipeline.telegram_newspaper_runner import (
    TELEGRAM_NEWSPAPER,
    newspaper_delivery_already_sent,
    publish_edition_newspaper_to_telegram,
)
from pipeline.telegram_audio_runner import (
    audio_delivery_already_sent,
    publish_edition_audio_to_telegram,
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


def build_edition_newspaper(
    edition: dict,
    *,
    output_root="data/newspaper",
) -> dict:
    """Render one approved edition into its complete newspaper pages."""

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

    safe_id = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        edition_id,
    ).strip("._") or "edition"

    root = Path(output_root) / safe_id

    try:
        rendered = render_edition(
            edition,
            root,
        )

        # Social-media publication uses the MOBILE presentation.
        # The FULL newspaper remains rendered separately for the future website.
        mobile = rendered.get("mobile_edition")
        if not isinstance(mobile, dict):
            return {
                "status": FAILED,
                "edition_id": edition_id,
                "reason": "MOBILE_RENDER_FAILED",
            }

        files = [
            str(path)
            for path in (mobile.get("pages") or [])
            if Path(path).is_file()
        ]

        if not files:
            return {
                "status": FAILED,
                "edition_id": edition_id,
                "reason": "NO_NEWSPAPER_PAGES",
            }

        return {
            "status": "GENERATED",
            "edition_id": edition_id,
            "page_count": len(files),
            "files": files,
            "output_root": str(root),
        }

    except Exception as exc:
        return {
            "status": FAILED,
            "edition_id": edition_id,
            "reason": "NEWSPAPER_RENDER_FAILED",
            "error": str(exc),
        }


def publish_edition(
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
    Build and publish one AROUND THE MAIN edition.

    Production order:
        1. build the reusable text publication package
        2. render newspaper PNG pages
        3. publish newspaper pages to Telegram
        4. generate Audio only after newspaper delivery is confirmed
        5. publish Audio to Telegram

    The reusable text publication package is intentionally retained and
    remains available to other social channels. It is not sent to Telegram
    by this production path.
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

    # Keep the complete text publication package for other social channels.
    # This production path deliberately does not send publication["telegram"].
    newspaper_delivery_identity = {
        "edition_id": publication.get("edition_id")
    }

    if newspaper_delivery_already_sent(
        publication.get("edition_id"),
        log=log,
    ):
        newspaper_result = {
            "status": "SKIPPED",
            "edition_id": publication.get("edition_id"),
            "reason": "ALREADY_SENT",
        }

        newspaper_delivery = {
            "status": "SKIPPED",
            "edition_id": publication.get("edition_id"),
            "reason": "ALREADY_SENT",
        }

    else:
        newspaper_result = build_edition_newspaper(
            edition,
            output_root=newspaper_output_root,
        )

        if newspaper_result.get("status") != "GENERATED":
            return {
                "status": FAILED,
                "reason": "NEWSPAPER_RENDER_FAILED",
                "edition_id": publication.get("edition_id"),
                "publication": publication,
                "newspaper": newspaper_result,
                "newspaper_delivery": None,
            }

        newspaper_sender = (
            newspaper_publisher
            if newspaper_publisher is not None
            else publish_edition_newspaper_to_telegram
        )

        newspaper_delivery = newspaper_sender(
            publication.get("edition_id"),
            newspaper_result.get("files", []),
            edition_number=edition.get("edition_number"),
            approval_manifest_path=approval_manifest_path,
            log=log,
        )

        # Production owns edition-level idempotency.
        # Record successful Newspaper delivery even when a custom publisher
        # (for example, the test publisher) does not write to the log itself.
        if newspaper_delivery.get("status") == "SENT":
            log.record_sent(
                newspaper_delivery_identity,
                TELEGRAM_NEWSPAPER,
            )

        if newspaper_delivery.get("status") not in {
            "SENT",
            "SKIPPED",
        }:
            return {
                "status": newspaper_delivery.get("status", FAILED),
                "edition_id": publication.get("edition_id"),
                "publication": publication,
                "newspaper": newspaper_result,
                "newspaper_delivery": newspaper_delivery,
                "audio": {
                    "status": "SKIPPED",
                    "edition_id": publication.get("edition_id"),
                    "reason": "NEWSPAPER_PUBLICATION_NOT_CONFIRMED",
                },
                "audio_delivery": None,
            }

    # Audio is generated only after the newspaper edition is confirmed.
    if edition.get("edition_number") is not None:

        # Never regenerate Audio that has already been delivered.
        if audio_delivery_already_sent(
            publication.get("edition_id"),
            log=log,
        ):
            audio_result = {
                "status": "SKIPPED",
                "edition_id": publication.get("edition_id"),
                "reason": "ALREADY_SENT",
            }

            audio_delivery = {
                "status": "SKIPPED",
                "edition_id": publication.get("edition_id"),
                "reason": "ALREADY_SENT",
            }

            return {
                "status": COMPLETED,
                "edition_id": publication.get("edition_id"),
                "publication": publication,
                "newspaper": newspaper_result,
                "newspaper_delivery": newspaper_delivery,
                "audio": audio_result,
                "audio_delivery": audio_delivery,
            }

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
                "newspaper": newspaper_result,
                "newspaper_delivery": newspaper_delivery,
                "audio": audio_result,
                "audio_delivery": None,
            }

        audio_sender = (
            audio_publisher
            if audio_publisher is not None
            else publish_edition_audio_to_telegram
        )

        audio_delivery = audio_sender(
            publication.get("edition_id"),
            audio_result.get("audio_path"),
            edition_number=edition.get("edition_number"),
            approval_manifest_path=approval_manifest_path,
            log=log,
        )

        return {
            "status": (
                COMPLETED
                if audio_delivery.get("status") == "SENT"
                else audio_delivery.get("status", FAILED)
            ),
            "edition_id": publication.get("edition_id"),
            "publication": publication,
            "newspaper": newspaper_result,
            "newspaper_delivery": newspaper_delivery,
            "audio": audio_result,
            "audio_delivery": audio_delivery,
        }

    audio_result = {
        "status": "SKIPPED",
        "edition_id": publication.get("edition_id"),
        "reason": "MISSING_EDITION_NUMBER",
    }

    return {
        "status": (
            COMPLETED
            if newspaper_delivery.get("status") in {"SENT", "SKIPPED"}
            else newspaper_delivery.get("status", FAILED)
        ),
        "edition_id": publication.get("edition_id"),
        "publication": publication,
        "newspaper": newspaper_result,
        "newspaper_delivery": newspaper_delivery,
        "audio": audio_result,
        "audio_delivery": None,
    }
