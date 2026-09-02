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
        "edition_id": "AROUND-THE-MAIN-EN-2026-08-30-1300",
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


def test_production_delivery_sends_edition(tmp_path):
    from tests.conftest import create_approved_manifest
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    result = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert result["status"] == "COMPLETED"
    assert result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )
    assert result["delivery"]["status"] == "SENT"
    assert result["publication"]["edition_type"] == "WORLD_PULSE"

    assert len(publisher.published) == 1

    log.close()


def test_production_delivery_is_idempotent(tmp_path):
    from tests.conftest import create_approved_manifest
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    first = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    second = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert first["status"] == "COMPLETED"
    assert second["status"] == "SKIPPED"
    assert len(publisher.published) == 1

    log.close()



def test_production_delivery_is_blocked_without_approval():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = deliver_production_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert result["status"] == "FAILED"
    assert result["edition_id"] == edition()["edition_id"]
    assert publisher.published == []

    log.close()


def test_invalid_edition_is_rejected():
    result = deliver_production_edition(None)

    assert result["status"] == "FAILED"
    assert result["reason"] == "INVALID_EDITION"


def test_production_delivery_does_not_modify_edition(tmp_path):
    from tests.conftest import create_approved_manifest
    item = edition()

    before = {
        "edition_id": item["edition_id"],
        "event_count": item["event_count"],
        "top_story": item["top_story"],
    }

    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    deliver_production_edition(
        item,
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert item["edition_id"] == before["edition_id"]
    assert item["event_count"] == before["event_count"]
    assert item["top_story"] == before["top_story"]

    log.close()
