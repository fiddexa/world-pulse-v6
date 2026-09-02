from pipeline.delivery_log import TELEGRAM, WEBSITE
from pipeline.delivery_executor import SENT, SKIPPED
from pipeline.orchestrator import deliver_events
from pipeline.delivery_log import DeliveryLog


class FakePublisher:
    def __init__(self):
        self.calls = []

    def publish(self, event):
        self.calls.append(event)

        return {
            "status": "SENT",
            "channel": TELEGRAM,
            "message_id": 123,
        }


def event():
    return {
        "editorial": {
            "decision": "STANDARD",
        },
        "content": {
            "headline": "AROUND THE MAIN TEST",
            "published_at": "2026-08-29T10:00:00Z",
            "sources": ["test-source"],
            "affected_areas": ["test"],
        },
        "publication": {
            "telegram": "AROUND THE MAIN TEST",
            "website": {
                "headline": "AROUND THE MAIN TEST",
            },
        },
    }


def test_deliver_events_sends_through_publisher():
    log = DeliveryLog()
    publisher = FakePublisher()

    results = deliver_events(
        [event()],
        log=log,
        publishers={
            TELEGRAM: publisher,
        },
        channels=[TELEGRAM],
    )

    assert len(results) == 1
    assert results[0][TELEGRAM]["status"] == SENT
    assert len(publisher.calls) == 1


def test_deliver_events_preserves_idempotency():
    log = DeliveryLog()
    publisher = FakePublisher()

    publishers = {
        TELEGRAM: publisher,
    }

    first = deliver_events(
        [event()],
        log=log,
        publishers=publishers,
        channels=[TELEGRAM],
    )

    second = deliver_events(
        [event()],
        log=log,
        publishers=publishers,
        channels=[TELEGRAM],
    )

    assert first[0][TELEGRAM]["status"] == SENT
    assert second[0][TELEGRAM]["status"] == SKIPPED
    assert len(publisher.calls) == 1


def test_deliver_events_handles_multiple_events():
    log = DeliveryLog()
    publisher = FakePublisher()

    events = [
        event(),
        {
            "editorial": {
                "decision": "STANDARD",
            },
            "publication": {
                "telegram": "SECOND TEST",
                "website": {
                    "headline": "SECOND TEST",
                },
            },
        },
    ]

    results = deliver_events(
        events,
        log=log,
        publishers={
            TELEGRAM: publisher,
        },
        channels=[TELEGRAM],
    )

    assert len(results) == 2
    assert results[0][TELEGRAM]["status"] == SENT
    assert results[1][TELEGRAM]["status"] == SENT
    assert len(publisher.calls) == 2


def test_invalid_events_are_ignored():
    results = deliver_events(
        [None, "invalid", 123],
    )

    assert results == []


def test_default_channels_remain_supported():
    log = DeliveryLog()

    results = deliver_events(
        [event()],
        log=log,
    )

    assert len(results) == 1
    assert TELEGRAM in results[0]
    assert WEBSITE in results[0]
