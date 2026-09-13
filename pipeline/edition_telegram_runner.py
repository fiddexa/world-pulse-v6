"""
AROUND THE MAIN v6 - Edition Telegram Runner

Publishes one complete AROUND THE MAIN edition publication package
to Telegram.

Event-level Telegram delivery remains handled by telegram_runner.py.
"""

from pipeline.edition_delivery_log import (
    SENT,
    TELEGRAM,
    SQLiteEditionDeliveryLog,
)
from pipeline.edition_approval import (
    APPROVAL_APPROVED,
    get_edition_approval_status,
)
from pipeline.telegram_factory import get_telegram_publisher


DEFAULT_EDITION_DELIVERY_LOG_PATH = (
    "data/edition_delivery.sqlite3"
)


def _get_default_log():
    return SQLiteEditionDeliveryLog(
        DEFAULT_EDITION_DELIVERY_LOG_PATH
    )


def _telegram_text(edition_publication):
    if not isinstance(edition_publication, dict):
        return ""

    telegram = edition_publication.get("telegram")

    if not isinstance(telegram, dict):
        return ""

    value = telegram.get("text")

    if value is None:
        return ""

    return str(value).strip()


TELEGRAM_MESSAGE_LIMIT = 4096


def _split_telegram_text(text, max_length=TELEGRAM_MESSAGE_LIMIT):
    """
    Split long Telegram text into safe message-sized chunks.

    Prefer paragraph boundaries so the editorial text remains readable.
    No chunk exceeds Telegram's sendMessage text limit.
    """
    text = str(text or "").strip()

    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        candidate = (
            paragraph
            if not current
            else current + "\n\n" + paragraph
        )

        if len(candidate) <= max_length:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= max_length:
            current = paragraph
            continue

        start = 0

        while start < len(paragraph):
            end = min(
                start + max_length,
                len(paragraph),
            )
            chunks.append(paragraph[start:end])
            start = end

    if current:
        chunks.append(current)

    return chunks


def _publisher_event(edition_publication, text):
    """
    Adapt one Telegram chunk to the existing
    TelegramPublisher interface.
    """
    return {
        "publication": {
            "telegram": str(text or "").strip()
        }
    }


def publish_edition_to_telegram(
    edition_publication,
    *,
    log=None,
    publisher=None,
    approval_manifest_path=None,
):
    """
    Publish one complete edition to Telegram.

    Edition-level idempotency is checked before the publisher
    is called.
    """
    if not isinstance(edition_publication, dict):
        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "reason": "INVALID_EDITION_PUBLICATION",
        }

    edition_id = str(
        edition_publication.get("edition_id", "")
    ).strip()

    if not edition_id:
        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "reason": "MISSING_EDITION_ID",
        }

    approval_status = get_edition_approval_status(
        edition_id,
        approval_manifest_path,
    )

    if approval_status != APPROVAL_APPROVED:
        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "edition_id": edition_id,
            "reason": "APPROVAL_NOT_APPROVED",
            "approval_status": approval_status,
        }

    text = _telegram_text(
        edition_publication
    )

    if not text:
        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "reason": "NO_CONTENT",
            "edition_id": edition_id,
        }

    if log is None:
        log = _get_default_log()

    if log.has_been_sent(
        edition_publication,
        TELEGRAM,
    ):
        return {
            "status": "SKIPPED",
            "channel": TELEGRAM,
            "edition_id": edition_id,
            "reason": "ALREADY_SENT",
        }

    if publisher is None:
        publisher = get_telegram_publisher()

    if publisher is None:
        log.record_failed(
            edition_publication,
            TELEGRAM,
        )

        return {
            "status": "NOT_CONFIGURED",
            "channel": TELEGRAM,
            "edition_id": edition_id,
        }

    chunks = _split_telegram_text(text)

    if not chunks:
        log.record_failed(
            edition_publication,
            TELEGRAM,
        )

        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "edition_id": edition_id,
            "reason": "NO_CONTENT",
        }

    results = []

    for index, chunk in enumerate(chunks, start=1):
        result = publisher.publish(
            _publisher_event(
                edition_publication,
                chunk,
            )
        )

        if not isinstance(result, dict):
            log.record_failed(
                edition_publication,
                TELEGRAM,
            )

            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "edition_id": edition_id,
                "reason": "INVALID_PUBLISHER_RESULT",
                "parts_sent": index - 1,
                "parts_total": len(chunks),
            }

        results.append(result)

        if result.get("status") != SENT:
            log.record_failed(
                edition_publication,
                TELEGRAM,
            )

            return {
                **result,
                "edition_id": edition_id,
                "parts_sent": index - 1,
                "parts_total": len(chunks),
                "failed_part": index,
            }

    log.record_sent(
        edition_publication,
        TELEGRAM,
    )

    message_ids = [
        item.get("message_id")
        for item in results
        if isinstance(item, dict)
        and item.get("message_id") is not None
    ]

    return {
        "status": SENT,
        "channel": TELEGRAM,
        "edition_id": edition_id,
        "parts_total": len(chunks),
        "message_ids": message_ids,
        "message_id": (
            message_ids[0]
            if len(message_ids) == 1
            else None
        ),
    }


def publish_editions_to_telegram(
    editions,
    *,
    log=None,
    publisher=None,
    approval_manifest_paths=None,
):
    """
    Publish multiple edition publication packages.
    """
    if not isinstance(editions, list):
        return []

    if log is None:
        log = _get_default_log()

    results = []

    for index, edition in enumerate(editions):
        if not isinstance(edition, dict):
            continue

        approval_manifest_path = None

        if isinstance(approval_manifest_paths, (list, tuple)):
            if index < len(approval_manifest_paths):
                approval_manifest_path = approval_manifest_paths[index]

        results.append(
            publish_edition_to_telegram(
                edition,
                log=log,
                publisher=publisher,
                approval_manifest_path=approval_manifest_path,
            )
        )

    return results
