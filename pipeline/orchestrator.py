"""
AROUND THE MAIN v6 - Production Orchestrator

Connects the prepared publication pipeline with delivery execution.

This layer:
- does not generate content;
- does not change editorial decisions;
- uses the existing delivery policy;
- uses DeliveryLog for idempotency;
- uses injected publishers;
- keeps external delivery explicit.
"""

from pipeline.delivery_executor import execute_event
from pipeline.delivery_log import DeliveryLog


def deliver_events(
    events,
    *,
    log=None,
    publishers=None,
    channels=None,
):
    """
    Execute delivery for prepared events.

    Returns one result dictionary per event.

    External publishing occurs only when publishers are explicitly
    supplied. Without publishers, the existing deterministic
    executor behavior is preserved.
    """

    if not isinstance(events, list):
        return []

    if log is None:
        log = DeliveryLog()

    results = []

    for event in events:
        if not isinstance(event, dict):
            continue

        result = execute_event(
            event,
            log,
            channels=channels,
            publishers=publishers,
        )

        results.append(result)

    return results
