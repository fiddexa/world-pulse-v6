from datetime import datetime

from pipeline.edition_delivery_log import (
    TELEGRAM,
    SQLiteEditionDeliveryLog,
)
from pipeline.production_delivery import (
    deliver_production_edition,
)
from pipeline.edition_preview import build_edition_preview, approve_edition_preview
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


def test_production_edition_can_be_delivered(tmp_path):
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
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )

    preview_root = tmp_path / "preview" / edition["edition_id"]

    preview_result = build_edition_preview(
        edition,
        preview_root,
    )

    assert preview_result["approval_status"] == "PENDING"

    approved_manifest = approve_edition_preview(
        preview_root,
    )

    assert approved_manifest["edition_id"] == edition["edition_id"]
    assert approved_manifest["approval_status"] == "APPROVED"

    delivery_result = deliver_production_edition(
        edition,
        log=delivery_log,
        publisher=publisher,
        approval_manifest_path=preview_result["manifest_path"],
    )

    assert delivery_result["status"] == "COMPLETED"
    assert delivery_result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )

    assert delivery_result["delivery"]["status"] == "SENT"
    assert len(publisher.published) == 1

    edition_memory.close()
    event_memory.close()
    delivery_log.close()


def test_production_edition_delivery_is_idempotent(tmp_path):
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

    preview_root = tmp_path / "preview" / edition["edition_id"]

    preview_result = build_edition_preview(
        edition,
        preview_root,
    )

    assert preview_result["approval_status"] == "PENDING"

    approve_edition_preview(preview_root)

    first = deliver_production_edition(
        edition,
        log=delivery_log,
        publisher=publisher,
        approval_manifest_path=preview_result["manifest_path"],
    )

    second = deliver_production_edition(
        edition,
        log=delivery_log,
        publisher=publisher,
        approval_manifest_path=preview_result["manifest_path"],
    )

    assert first["status"] == "COMPLETED"
    assert second["status"] == "SKIPPED"

    assert len(publisher.published) == 1

    edition_memory.close()
    event_memory.close()
    delivery_log.close()
