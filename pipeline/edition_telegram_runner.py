"""
WORLD PULSE v6 - Edition Telegram Runner

Publishes one complete WORLD PULSE edition publication package
to Telegram.

Event-level Telegram delivery remains handled by telegram_runner.py.
"""

from pipeline.edition_delivery_log import (
    SENT,
    TELEGRAM,
    SQLiteEditionDeliveryLog,
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


def _publisher_event(edition_publication):
    """
    Adapt an edition publication package to the existing
    TelegramPublisher interface without modifying the package.
    """
    return {
        "publication": {
            "telegram": _telegram_text(
                edition_publication
            )
        }
    }


def publish_edition_to_telegram(
    edition_publication,
    *,
    log=None,
    publisher=None,
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

    result = publisher.publish(
        _publisher_event(
            edition_publication
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
        }

    status = result.get("status")

    if status == SENT:
        log.record_sent(
            edition_publication,
            TELEGRAM,
        )

        return {
            **result,
            "edition_id": edition_id,
        }

    if status == "FAILED":
        log.record_failed(
            edition_publication,
            TELEGRAM,
        )

    return {
        **result,
        "edition_id": edition_id,
    }


def publish_editions_to_telegram(
    editions,
    *,
    log=None,
    publisher=None,
):
    """
    Publish multiple edition publication packages.
    """
    if not isinstance(editions, list):
        return []

    if log is None:
        log = _get_default_log()

    results = []

    for edition in editions:
        if not isinstance(edition, dict):
            continue

        results.append(
            publish_edition_to_telegram(
                edition,
                log=log,
                publisher=publisher,
            )
        )

    return results
