"""
AROUND THE MAIN — Telegram Audio Runner

Edition-level audio delivery with approval and idempotency hooks.
"""
from __future__ import annotations

from pathlib import Path
import json
import os
import urllib.error
import urllib.request

from pipeline.edition_approval import (
    APPROVAL_APPROVED,
    get_edition_approval_status,
)


def _telegram_send_audio(
    *,
    chat_id: str,
    audio_path: str,
) -> dict:
    """Send an MP3 file through the Telegram Bot API."""

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not token:
        return {
            "ok": False,
            "error": "TELEGRAM_BOT_TOKEN is not configured",
        }

    url = (
        f"https://api.telegram.org/bot{token}/sendAudio"
    )

    boundary = "----AROUND-THE-MAIN-AUDIO"

    audio_file = Path(audio_path)
    audio_bytes = audio_file.read_bytes()

    fields = {
        "chat_id": str(chat_id),
    }

    body = bytearray()

    for name, value in fields.items():
        body.extend(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n'
                "\r\n"
                f"{value}\r\n"
            ).encode("utf-8")
        )

    body.extend(
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; '
            'name="audio"; filename="around-the-main.mp3"\r\n'
            "Content-Type: audio/mpeg\r\n"
            "\r\n"
        ).encode("utf-8")
    )

    body.extend(audio_bytes)
    body.extend(
        f"\r\n--{boundary}--\r\n".encode("utf-8")
    )

    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Content-Type": (
                f"multipart/form-data; boundary={boundary}"
            )
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:
            raw = response.read().decode(
                "utf-8",
                errors="replace",
            )

        return json.loads(raw)

    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        return {
            "ok": False,
            "error": f"Telegram HTTP {exc.code}",
            "response": raw,
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


def publish_edition_audio_to_telegram(
    edition_id: str,
    audio_path: str | Path,
    *,
    approval_manifest_path=None,
    transport=None,
    chat_id=None,
):
    """Publish one approved edition audio file through an injected transport."""

    edition_id = str(edition_id or "").strip()
    audio_file = Path(audio_path)

    if not edition_id:
        return {
            "status": "FAILED",
            "reason": "MISSING_EDITION_ID",
        }

    approval_status = get_edition_approval_status(
        edition_id,
        approval_manifest_path,
    )

    if approval_status != APPROVAL_APPROVED:
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "APPROVAL_NOT_APPROVED",
            "approval_status": approval_status,
        }

    if not audio_file.is_file():
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "AUDIO_FILE_NOT_FOUND",
        }

    if transport is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

        if not token:
            return {
                "status": "NOT_CONFIGURED",
                "edition_id": edition_id,
            }

        if not chat_id:
            chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

        if not chat_id:
            return {
                "status": "NOT_CONFIGURED",
                "edition_id": edition_id,
            }

        transport = _telegram_send_audio

    if not chat_id:
        return {
            "status": "NOT_CONFIGURED",
            "edition_id": edition_id,
        }

    response = transport(
        chat_id=chat_id,
        audio_path=str(audio_file),
    )

    if isinstance(response, dict) and response.get("ok") is True:
        return {
            "status": "SENT",
            "edition_id": edition_id,
            "message_id": (
                response.get("result", {}).get("message_id")
                if isinstance(response.get("result"), dict)
                else None
            ),
        }

    return {
        "status": "FAILED",
        "edition_id": edition_id,
        "reason": "TELEGRAM_API_ERROR",
        "response": response,
    }
