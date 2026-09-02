"""
AROUND THE MAIN v6 - Telegram Runner

Explicit production entry point for Telegram delivery.

This module is intentionally separate from process_articles():
normal processing must never publish externally by accident.

Production delivery uses persistent SQLite delivery memory by
default so SENT/FAILED state survives process restarts.

Tests and controlled execution may inject another DeliveryLog.
"""

from pipeline.delivery_executor import execute_delivery
from pipeline.delivery_log import DeliveryLog, TELEGRAM
from pipeline.sqlite_delivery_log import SQLiteDeliveryLog
from pipeline.telegram_factory import get_telegram_publisher


DEFAULT_DELIVERY_LOG_PATH = "data/telegram_delivery.sqlite3"


def _get_default_log():
    """
    Return the persistent production delivery log.
    """

    return SQLiteDeliveryLog(
        DEFAULT_DELIVERY_LOG_PATH
    )


def publish_event_to_telegram(event, *, log=None):
    """
    Publish one prepared event to Telegram.

    When log is omitted, persistent SQLite delivery memory
    is used.

    Returns the executor result.
    """

    if not isinstance(event, dict):
        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "reason": "INVALID_EVENT",
        }

    if log is None:
        log = _get_default_log()

    publisher = get_telegram_publisher()

    if publisher is None:
        return {
            "status": "NOT_CONFIGURED",
            "channel": TELEGRAM,
        }

    return execute_delivery(
        event,
        TELEGRAM,
        log,
        publisher=publisher,
    )


def publish_events_to_telegram(events, *, log=None):
    """
    Publish a list of prepared events.

    Uses one delivery log for the whole batch so duplicate
    protection works across all events in the batch.

    When log is omitted, persistent SQLite delivery memory
    is used.
    """

    if not isinstance(events, list):
        return []

    if log is None:
        log = _get_default_log()

    results = []

    for event in events:
        if not isinstance(event, dict):
            continue

        results.append(
            publish_event_to_telegram(
                event,
                log=log,
            )
        )

    return results
