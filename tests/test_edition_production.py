from pathlib import Path

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


def test_publish_edition_builds_package_and_delivers(tmp_path):
    from tests.conftest import create_approved_manifest
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    result = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert result["status"] == COMPLETED
    assert result["edition_id"] == (
        "AROUND-THE-MAIN-EN-2026-08-30-1300"
    )

    assert result["publication"]["telegram"]["text"]
    assert result["delivery"]["status"] == "SENT"

    assert len(publisher.published) == 1

    log.close()


def test_publish_edition_is_idempotent(tmp_path):
    from tests.conftest import create_approved_manifest
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    first = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    second = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert first["status"] == COMPLETED
    assert second["status"] == "SKIPPED"

    assert len(publisher.published) == 1

    log.close()



def test_publish_edition_is_blocked_without_approval():
    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition(
        edition(),
        log=log,
        publisher=publisher,
    )

    assert result["status"] == FAILED
    assert result["reason"] == "APPROVAL_NOT_APPROVED"
    assert result["approval_status"] is None
    assert publisher.published == []

    log.close()


def test_invalid_edition_is_rejected():
    result = publish_edition(None)

    assert result["status"] == FAILED
    assert result["reason"] == "INVALID_EDITION"


def test_original_edition_is_not_modified(tmp_path):
    from tests.conftest import create_approved_manifest
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
    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    publish_edition(
        item,
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert item["edition_id"] == before["edition_id"]
    assert item["event_count"] == before["event_count"]
    assert item["top_story"] == before["top_story"]
    assert item["main_stories"] == before["main_stories"]
    assert item["briefs"] == before["briefs"]

    log.close()


def test_failed_delivery_does_not_report_completed(tmp_path):
    from tests.conftest import create_approved_manifest
    class FailedPublisher:
        def publish(self, event):
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "TEST_FAILURE",
            }

    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    result = publish_edition(
        edition(),
        log=log,
        publisher=FailedPublisher(),
        approval_manifest_path=approval_manifest,
    )

    assert result["status"] == "FAILED"
    assert result["delivery"]["status"] == "FAILED"

    log.close()

def test_publish_edition_text_before_audio(tmp_path, monkeypatch):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    item = edition()
    item["edition_number"] = 114

    publisher = MockPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    calls = []

    def fake_generate_audio(
        edition,
        *,
        output_dir,
        audio_renderer=None,
    ):
        calls.append("audio_generate")
        audio_path = tmp_path / "EDITION_0114.mp3"
        audio_path.write_bytes(b"fake-audio")

        return {
            "status": "GENERATED",
            "edition_id": edition["edition_id"],
            "audio_path": str(audio_path),
        }

    def fake_audio_publish(
        edition_id,
        audio_path,
        *,
        edition_number,
        approval_manifest_path,
    ):
        calls.append(
            f"audio_publish:{edition_number}"
        )

        assert calls[0] == "text_publish"
        assert Path(audio_path).is_file()

        return {
            "status": "SENT",
            "edition_id": edition_id,
            "message_id": 789,
        }

    class OrderedPublisher(MockPublisher):
        def publish(self, event):
            calls.append("text_publish")
            return super().publish(event)

    publisher = OrderedPublisher()

    monkeypatch.setattr(
        production,
        "generate_edition_audio",
        fake_generate_audio,
    )

    result = production.publish_edition(
        item,
        log=log,
        publisher=publisher,
        approval_manifest_path=approval_manifest,
        audio_publisher=fake_audio_publish,
    )

    assert result["status"] == COMPLETED
    assert result["delivery"]["status"] == "SENT"
    assert result["audio"]["status"] == "GENERATED"
    assert result["audio_delivery"]["status"] == "SENT"

    assert calls == [
        "text_publish",
        "audio_generate",
        "audio_publish:114",
    ]

    log.close()
