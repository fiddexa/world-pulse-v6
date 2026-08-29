"""
WORLD PULSE v6 - Telegram Runner

Explicit production entry point for Telegram delivery.

This module is intentionally separate from process_articles():
normal processing must never publish externally by accident.
"""

from pipeline.delivery_executor import execute_delivery
from pipeline.delivery_log import DeliveryLog, TELEGRAM
from pipeline.telegram_factory import get_telegram_publisher


def publish_event_to_telegram(event, *, log=None):
    """
    Publish one prepared event to Telegram.

    Returns the executor result.
    """

    if not isinstance(event, dict):
        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "reason": "INVALID_EVENT",
        }

    if log is None:
        log = DeliveryLog()

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

    Uses one DeliveryLog for the whole batch so duplicate
    protection works across all events in the batch.
    """

    if not isinstance(events, list):
        return []

    if log is None:
        log = DeliveryLog()

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
