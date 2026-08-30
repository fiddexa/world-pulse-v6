"""
WORLD PULSE v6 - Delivery Executor

Coordinates delivery policy, idempotency state, and publishers.

The publisher is injectable so delivery can be tested without
external network calls.
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
    publisher=None,
):
    """
    Execute delivery for one channel.

    When a publisher is supplied, its publish() result determines
    whether the delivery is recorded as SENT or FAILED.

    When no publisher is supplied, the original deterministic
    simulation behavior is preserved.
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

    if publisher is not None:
        result = publisher.publish(event)

        if not isinstance(result, dict):
            log.record_failed(event, channel)

            return {
                "status": "FAILED",
                "channel": channel,
                "reason": "INVALID_PUBLISHER_RESULT",
            }

        published_status = result.get("status")

        if published_status == SENT:
            log.record_sent(event, channel)

            return {
                **result,
                "status": SENT,
                "channel": channel,
            }

        log.record_failed(event, channel)

        return {
            **result,
            "status": "FAILED",
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
    publishers=None,
):
    """
    Execute delivery for the requested channels.

    `publishers` is an optional mapping:
        {
            "telegram": TelegramPublisher(...),
            "website": WebsitePublisher(...),
        }

    Without publishers, deterministic simulation is preserved.
    """

    if channels is None:
        channels = [
            TELEGRAM,
            WEBSITE,
        ]

    if not isinstance(channels, list):
        channels = []

    if not isinstance(publishers, dict):
        publishers = {}

    results = {}

    for channel in channels:
        publisher = publishers.get(channel)

        results[channel] = execute_delivery(
            event,
            channel,
            log,
            publisher=publisher,
        )

    return results
