"""
WORLD PULSE v6 - Delivery Executor

Coordinates delivery policy and idempotency state.

This layer does not perform external network delivery yet.
It provides a deterministic execution decision for future
Telegram/Website publishers.
"""

from pipeline.delivery import delivery_policy
from pipeline.delivery_log import (
    DeliveryLog,
    SENT,
    TELEGRAM,
    WEBSITE,
)


SKIPPED = "SKIPPED"
READY = "READY"
BLOCKED = "BLOCKED"


def _channel_policy(event, channel):
    policy = delivery_policy(event)

    value = policy.get(channel)

    return value if isinstance(value, dict) else {}


def execution_status(
    event,
    channel,
    log,
):
    """
    Determine whether an event should be executed for a channel.
    """

    if not isinstance(log, DeliveryLog):
        raise TypeError("log must be a DeliveryLog")

    channel_policy = _channel_policy(
        event,
        channel,
    )

    if not channel_policy.get("allowed", False):
        return BLOCKED

    if log.has_been_sent(event, channel):
        return SKIPPED

    return READY


def execute_delivery(
    event,
    channel,
    log,
    success=True,
):
    """
    Execute a simulated delivery.

    No external network call is made.
    """

    status = execution_status(
        event,
        channel,
        log,
    )

    if status == BLOCKED:
        return {
            "status": BLOCKED,
            "channel": channel,
        }

    if status == SKIPPED:
        return {
            "status": SKIPPED,
            "channel": channel,
        }

    if success:
        log.record_sent(event, channel)

        return {
            "status": SENT,
            "channel": channel,
        }

    log.record_failed(event, channel)

    return {
        "status": "FAILED",
        "channel": channel,
    }


def execute_event(
    event,
    log,
    channels=None,
):
    """
    Simulate delivery for the requested channels.
    """

    if channels is None:
        channels = [
            TELEGRAM,
            WEBSITE,
        ]

    if not isinstance(channels, list):
        channels = []

    results = {}

    for channel in channels:
        results[channel] = execute_delivery(
            event,
            channel,
            log,
        )

    return results
