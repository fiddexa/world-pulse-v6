from pipeline.edition_production import (
    COMPLETED,
    FAILED,
    publish_edition,
)
from pipeline.edition_delivery_log import (
    TELEGRAM,
    SQLiteEditionDeliveryLog,
)


class MockPublisher:
    def __init__(self):
        self.published = []

    def publish(self, event):
        self.published.append(event)

        return {
            "status": "SENT",
            "channel": TELEGRAM,
            "message_id": 456,
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


def test_publish_edition_builds_package_and_delivers():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert result["status"] == COMPLETED
    assert result["edition_id"] == (
        "WORLD-PULSE-EN-2026-08-30-1300"
    )

    assert result["publication"]["telegram"]["text"]
    assert result["delivery"]["status"] == "SENT"

    assert len(publisher.published) == 1

    log.close()


def test_publish_edition_is_idempotent():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    first = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    second = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert first["status"] == COMPLETED
    assert second["status"] == "SKIPPED"

    assert len(publisher.published) == 1

    log.close()


def test_invalid_edition_is_rejected():
    result = publish_edition(None)

    assert result["status"] == FAILED
    assert result["reason"] == "INVALID_EDITION"


def test_original_edition_is_not_modified():
    item = edition()

    before = {
        "edition_id": item["edition_id"],
        "event_count": item["event_count"],
        "top_story": item["top_story"],
        "main_stories": item["main_stories"],
        "briefs": item["briefs"],
    }

    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    publish_edition(
        item,
        log=log,
        publisher=publisher,
    )

    assert item["edition_id"] == before["edition_id"]
    assert item["event_count"] == before["event_count"]
    assert item["top_story"] == before["top_story"]
    assert item["main_stories"] == before["main_stories"]
    assert item["briefs"] == before["briefs"]

    log.close()


def test_failed_delivery_does_not_report_completed():
    class FailedPublisher:
        def publish(self, event):
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "TEST_FAILURE",
            }

    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition(
        edition(),
        log=log,
        publisher=FailedPublisher(),
    )

    assert result["status"] == "FAILED"
    assert result["delivery"]["status"] == "FAILED"

    log.close()
