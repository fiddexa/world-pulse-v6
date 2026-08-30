from datetime import datetime

from pipeline.edition_delivery_log import (
    TELEGRAM,
    SQLiteEditionDeliveryLog,
)
from pipeline.production_delivery import (
    deliver_production_edition,
)
from pipeline.production_job import run_production_job
from pipeline.edition_memory import EditionMemory
from pipeline.event_memory import EventMemory


class MockPublisher:
    def __init__(self):
        self.published = []

    def publish(self, event):
        self.published.append(event)

        return {
            "status": "SENT",
            "channel": TELEGRAM,
            "message_id": 1001,
        }


def articles():
    return [
        {
            "title": "Major earthquake strikes Nepal",
            "summary": "A powerful earthquake hits Nepal.",
            "published_at": "2026-08-28T10:00:00Z",
            "source": "Reuters",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
        {
            "title": "Strong earthquake hits Nepal",
            "summary": "The earthquake causes widespread damage.",
            "published_at": "2026-08-28T10:20:00Z",
            "source": "BBC",
            "category": "world",
            "region": "asia",
            "country": "nepal",
        },
    ]


def test_production_edition_can_be_delivered():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")
    delivery_log = SQLiteEditionDeliveryLog(":memory:")
    publisher = MockPublisher()

    production_result = run_production_job(
        articles(),
        datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    assert production_result["status"] == "COMPLETED"

    edition = production_result["edition"]

    assert edition["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    delivery_result = deliver_production_edition(
        edition,
        log=delivery_log,
        publisher=publisher,
    )

    assert delivery_result["status"] == "COMPLETED"
    assert delivery_result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    assert delivery_result["delivery"]["status"] == "SENT"
    assert len(publisher.published) == 1

    edition_memory.close()
    event_memory.close()
    delivery_log.close()


def test_production_edition_delivery_is_idempotent():
    edition_memory = EditionMemory(":memory:")
    event_memory = EventMemory(":memory:")
    delivery_log = SQLiteEditionDeliveryLog(":memory:")
    publisher = MockPublisher()

    production_result = run_production_job(
        articles(),
        datetime(
            2026,
            8,
            30,
            13,
            45,
        ),
        edition_memory=edition_memory,
        event_memory=event_memory,
    )

    edition = production_result["edition"]

    first = deliver_production_edition(
        edition,
        log=delivery_log,
        publisher=publisher,
    )

    second = deliver_production_edition(
        edition,
        log=delivery_log,
        publisher=publisher,
    )

    assert first["status"] == "COMPLETED"
    assert second["status"] == "SKIPPED"

    assert len(publisher.published) == 1

    edition_memory.close()
    event_memory.close()
    delivery_log.close()
