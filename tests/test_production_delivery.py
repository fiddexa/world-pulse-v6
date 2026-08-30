from pipeline.edition_delivery_log import (
    TELEGRAM,
    SQLiteEditionDeliveryLog,
)
from pipeline.production_delivery import (
    deliver_production_edition,
)


class MockPublisher:
    def __init__(self):
        self.published = []

    def publish(self, event):
        self.published.append(event)

        return {
            "status": "SENT",
            "channel": TELEGRAM,
            "message_id": 789,
        }


def edition():
    return {
        "edition_id": "WORLD-PULSE-EN-2026-08-30-1300",
        "edition_type": "WORLD_PULSE",
        "event_count": 1,
        "top_story": {
            "editorial": {
                "role": "TOP_STORY",
            },
            "content": {
                "headline": "Major earthquake",
                "section": "world",
            },
            "publication": {
                "telegram": "Major earthquake",
            },
        },
        "main_stories": [],
        "briefs": [],
    }


def test_production_delivery_sends_edition():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert result["status"] == "COMPLETED"
    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )
    assert result["delivery"]["status"] == "SENT"
    assert result["publication"]["edition_type"] == "WORLD_PULSE"

    assert len(publisher.published) == 1

    log.close()


def test_production_delivery_is_idempotent():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    first = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    second = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert first["status"] == "COMPLETED"
    assert second["status"] == "SKIPPED"
    assert len(publisher.published) == 1

    log.close()


def test_invalid_edition_is_rejected():
    result = deliver_production_edition(None)

    assert result["status"] == "FAILED"
    assert result["reason"] == "INVALID_EDITION"


def test_production_delivery_does_not_modify_edition():
    item = edition()

    before = {
        "edition_id": item["edition_id"],
        "event_count": item["event_count"],
        "top_story": item["top_story"],
    }

    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    deliver_production_edition(
        item,
        log=log,
        publisher=publisher,
    )

    assert item["edition_id"] == before["edition_id"]
    assert item["event_count"] == before["event_count"]
    assert item["top_story"] == before["top_story"]

    log.close()
