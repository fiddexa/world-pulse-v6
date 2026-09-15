"""
AROUND THE MAIN — Telegram Newspaper Runner

Edition-level newspaper image delivery with approval and persistent
idempotency hooks.
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
from pipeline.edition_delivery_log import (
    TELEGRAM_NEWSPAPER,
    SQLiteEditionDeliveryLog,
)


DEFAULT_NEWSPAPER_DELIVERY_LOG_PATH = (
    "data/edition_delivery.sqlite3"
)


def _get_default_newspaper_log():
    return SQLiteEditionDeliveryLog(
        DEFAULT_NEWSPAPER_DELIVERY_LOG_PATH
    )


def _newspaper_identity(edition_id: str) -> dict:
    return {
        "edition_id": str(edition_id or "").strip()
    }


def newspaper_delivery_already_sent(
    edition_id: str,
    *,
    log=None,
) -> bool:
    edition_id = str(edition_id or "").strip()

    if not edition_id:
        return False

    if log is None:
        log = _get_default_newspaper_log()

    return log.has_been_sent(
        _newspaper_identity(edition_id),
        TELEGRAM_NEWSPAPER,
    )


def _telegram_send_photo(
    *,
    chat_id: str,
    photo_path: str,
    caption: str = "",
) -> dict:
    """Send one newspaper page through the Telegram Bot API."""

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not token:
        return {
            "ok": False,
            "error": "TELEGRAM_BOT_TOKEN is not configured",
        }

    url = (
        f"https://api.telegram.org/bot{token}/sendPhoto"
    )

    boundary = "----AROUND-THE-MAIN-NEWSPAPER"

    photo_file = Path(photo_path)
    photo_bytes = photo_file.read_bytes()

    fields = {
        "chat_id": str(chat_id),
    }

    if caption:
        fields["caption"] = str(caption)

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
            'name="photo"; filename="around-the-main.png"\r\n'
            "Content-Type: image/png\r\n"
            "\r\n"
        ).encode("utf-8")
    )

    body.extend(photo_bytes)
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


def publish_edition_newspaper_to_telegram(
    edition_id: str,
    page_paths,
    *,
    edition_number=None,
    approval_manifest_path=None,
    transport=None,
    chat_id=None,
    log=None,
):
    """Publish all rendered newspaper PNG pages for one approved edition."""

    edition_id = str(edition_id or "").strip()

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

    pages = []
    for value in page_paths or []:
        path = Path(value)
        if path.is_file():
            pages.append(path)

    if not pages:
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "NO_NEWSPAPER_PAGES",
        }

    if log is None:
        log = _get_default_newspaper_log()

    identity = _newspaper_identity(edition_id)

    if log.has_been_sent(
        identity,
        TELEGRAM_NEWSPAPER,
    ):
        return {
            "status": "SKIPPED",
            "edition_id": edition_id,
            "reason": "ALREADY_SENT",
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

        transport = _telegram_send_photo

    if not chat_id:
        return {
            "status": "NOT_CONFIGURED",
            "edition_id": edition_id,
        }

    try:
        number = (
            int(edition_number)
            if edition_number is not None
            else None
        )
    except (TypeError, ValueError):
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "INVALID_EDITION_NUMBER",
        }

    message_ids = []
    total = len(pages)

    for index, page in enumerate(pages, start=1):
        # Telegram publication is image-only.
        # No caption/text block is attached below the newspaper page.
        caption = ""

        response = transport(
            chat_id=chat_id,
            photo_path=str(page),
            caption=caption,
        )

        if not (
            isinstance(response, dict)
            and response.get("ok") is True
        ):
            log.record_failed(
                identity,
                TELEGRAM_NEWSPAPER,
            )

            return {
                "status": "FAILED",
                "edition_id": edition_id,
                "reason": "TELEGRAM_API_ERROR",
                "page_number": index,
                "pages_sent": len(message_ids),
                "pages_total": total,
                "response": response,
            }

        result = response.get("result")
        message_id = (
            result.get("message_id")
            if isinstance(result, dict)
            else None
        )
        message_ids.append(message_id)

    log.record_sent(
        identity,
        TELEGRAM_NEWSPAPER,
    )

    return {
        "status": "SENT",
        "edition_id": edition_id,
        "pages_total": total,
        "message_ids": message_ids,
    }
