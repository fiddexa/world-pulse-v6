"""
AROUND THE MAIN — Edition Audio

Generates the final audio file for one edition.

The human-facing edition number is allocated by the production
scheduler and stored in edition["edition_number"].

Filename convention:
    EDITION_0001.mp3
    EDITION_0002.mp3
    EDITION_0003.mp3
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.audio_renderer import PiperTTSRenderer
from pipeline.audio_script import build_audio_script


def edition_audio_filename(edition: dict[str, Any]) -> str:
    """Return the canonical audio filename using edition_number."""

    if not isinstance(edition, dict):
        raise ValueError("edition must be a dictionary")

    number = edition.get("edition_number")

    if isinstance(number, bool):
        raise ValueError("edition_number must be an integer")

    try:
        number = int(number)
    except (TypeError, ValueError):
        raise ValueError(
            "edition_number is required for audio filename"
        )

    if number < 0:
        raise ValueError(
            "edition_number must not be negative"
        )

    return f"EDITION_{number:04d}.mp3"


def generate_edition_audio(
    edition: dict[str, Any],
    *,
    output_dir: str | Path = "data/audio",
    audio_renderer=None,
) -> dict[str, Any]:
    """Generate one complete audio file from one edition."""

    if not isinstance(edition, dict):
        return {
            "status": "FAILED",
            "reason": "INVALID_EDITION",
        }

    edition_id = str(
        edition.get("edition_id") or ""
    ).strip()

    if not edition_id:
        return {
            "status": "FAILED",
            "reason": "MISSING_EDITION_ID",
        }

    if edition.get("edition_number") is None:
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "MISSING_EDITION_NUMBER",
        }

    try:
        script = build_audio_script(edition)

        if not script.strip():
            return {
                "status": "FAILED",
                "edition_id": edition_id,
                "reason": "EMPTY_AUDIO_SCRIPT",
            }

        filename = edition_audio_filename(edition)
        output = Path(output_dir) / filename

        renderer = (
            audio_renderer
            if audio_renderer is not None
            else PiperTTSRenderer()
        )

        rendered = renderer.render(
            script,
            output,
        )

        return {
            "status": "GENERATED",
            "edition_id": edition_id,
            "edition_number": int(
                edition["edition_number"]
            ),
            "audio_path": str(rendered),
            "filename": filename,
            "script": script,
        }

    except Exception as exc:
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "AUDIO_GENERATION_FAILED",
            "error": str(exc),
        }
