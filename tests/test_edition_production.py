from pathlib import Path

from pipeline.edition_production import (
    COMPLETED,
    FAILED,
    publish_edition,
)
from pipeline.edition_delivery_log import (
    TELEGRAM_NEWSPAPER,
    TELEGRAM_AUDIO,
    SQLiteEditionDeliveryLog,
)


class MockNewspaperPublisher:
    def __init__(self):
        self.published = []

    def __call__(
        self,
        edition_id,
        page_paths,
        *,
        edition_number,
        approval_manifest_path,
        log,
    ):
        self.published.append(
            {
                "edition_id": edition_id,
                "page_paths": list(page_paths),
                "edition_number": edition_number,
            }
        )
        return {
            "status": "SENT",
            "channel": TELEGRAM_NEWSPAPER,
            "pages_total": len(page_paths),
            "message_ids": list(
                range(100, 100 + len(page_paths))
            ),
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


def test_publish_edition_builds_text_package_and_delivers_newspaper(
    tmp_path,
    monkeypatch,
):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    publisher = MockNewspaperPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    def fake_build_newspaper(
        item,
        *,
        output_root,
    ):
        path = tmp_path / "page-01.png"
        path.write_bytes(b"png")
        return {
            "status": "GENERATED",
            "edition_id": item["edition_id"],
            "page_count": 1,
            "files": [str(path)],
            "output_root": str(tmp_path),
        }

    monkeypatch.setattr(
        production,
        "build_edition_newspaper",
        fake_build_newspaper,
    )

    result = publish_edition(
        edition(),
        log=log,
        newspaper_publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert result["status"] == COMPLETED
    assert result["publication"]["telegram"]["text"]
    assert result["newspaper_delivery"]["status"] == "SENT"
    assert result["audio"]["status"] == "SKIPPED"
    assert result["audio"]["reason"] == "MISSING_EDITION_NUMBER"
    assert len(publisher.published) == 1
    assert len(publisher.published[0]["page_paths"]) == 1

    log.close()


def test_publish_edition_is_idempotent_for_newspaper(tmp_path, monkeypatch):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    item = edition()
    publisher = MockNewspaperPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    def fake_build_newspaper(
        item,
        *,
        output_root,
    ):
        path = tmp_path / "page-01.png"
        path.write_bytes(b"png")
        return {
            "status": "GENERATED",
            "edition_id": item["edition_id"],
            "page_count": 1,
            "files": [str(path)],
            "output_root": str(tmp_path),
        }

    monkeypatch.setattr(
        production,
        "build_edition_newspaper",
        fake_build_newspaper,
    )

    first = publish_edition(
        item,
        log=log,
        newspaper_publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    second = publish_edition(
        item,
        log=log,
        newspaper_publisher=publisher,
        approval_manifest_path=approval_manifest,
    )

    assert first["status"] == COMPLETED
    assert second["status"] == COMPLETED
    assert second["newspaper"]["status"] == "SKIPPED"
    assert second["newspaper"]["reason"] == "ALREADY_SENT"
    assert second["newspaper_delivery"]["status"] == "SKIPPED"
    assert len(publisher.published) == 1

    log.close()


def test_publish_edition_is_blocked_without_approval():
    publisher = MockNewspaperPublisher()
    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition(
        edition(),
        log=log,
        newspaper_publisher=publisher,
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


def test_original_edition_is_not_modified(tmp_path, monkeypatch):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    item = edition()

    before = {
        "edition_id": item["edition_id"],
        "event_count": item["event_count"],
        "top_story": item["top_story"],
        "main_stories": item["main_stories"],
        "briefs": item["briefs"],
    }

    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    def fake_build_newspaper(
        item,
        *,
        output_root,
    ):
        path = tmp_path / "page-01.png"
        path.write_bytes(b"png")
        return {
            "status": "GENERATED",
            "edition_id": item["edition_id"],
            "page_count": 1,
            "files": [str(path)],
        }

    monkeypatch.setattr(
        production,
        "build_edition_newspaper",
        fake_build_newspaper,
    )

    publish_edition(
        item,
        log=log,
        newspaper_publisher=MockNewspaperPublisher(),
        approval_manifest_path=approval_manifest,
    )

    assert item["edition_id"] == before["edition_id"]
    assert item["event_count"] == before["event_count"]
    assert item["top_story"] == before["top_story"]
    assert item["main_stories"] == before["main_stories"]
    assert item["briefs"] == before["briefs"]

    log.close()


def test_failed_newspaper_delivery_does_not_report_completed(
    tmp_path,
    monkeypatch,
):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        edition()["edition_id"],
    )

    def fake_build_newspaper(
        item,
        *,
        output_root,
    ):
        path = tmp_path / "page-01.png"
        path.write_bytes(b"png")
        return {
            "status": "GENERATED",
            "edition_id": item["edition_id"],
            "page_count": 1,
            "files": [str(path)],
        }

    monkeypatch.setattr(
        production,
        "build_edition_newspaper",
        fake_build_newspaper,
    )

    def failed_publisher(
        edition_id,
        page_paths,
        *,
        edition_number,
        approval_manifest_path,
        log,
    ):
        return {
            "status": "FAILED",
            "channel": TELEGRAM_NEWSPAPER,
            "reason": "TEST_FAILURE",
        }

    result = publish_edition(
        edition(),
        log=log,
        newspaper_publisher=failed_publisher,
        approval_manifest_path=approval_manifest,
    )

    assert result["status"] == "FAILED"
    assert result["newspaper_delivery"]["status"] == "FAILED"
    assert result["audio"]["status"] == "SKIPPED"
    assert result["audio"]["reason"] == (
        "NEWSPAPER_PUBLICATION_NOT_CONFIRMED"
    )

    log.close()


def test_publish_edition_newspaper_before_audio(tmp_path, monkeypatch):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    item = edition()
    item["edition_number"] = 114

    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    calls = []

    def fake_build_newspaper(
        item,
        *,
        output_root,
    ):
        calls.append("newspaper_generate")
        page = tmp_path / "page-01.png"
        page.write_bytes(b"png")
        return {
            "status": "GENERATED",
            "edition_id": item["edition_id"],
            "page_count": 1,
            "files": [str(page)],
        }

    def fake_newspaper_publish(
        edition_id,
        page_paths,
        *,
        edition_number,
        approval_manifest_path,
        log,
    ):
        calls.append("newspaper_publish")
        assert page_paths
        assert calls == [
            "newspaper_generate",
            "newspaper_publish",
        ]
        return {
            "status": "SENT",
            "edition_id": edition_id,
        }

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
        log,
    ):
        calls.append(f"audio_publish:{edition_number}")
        assert calls[:3] == [
            "newspaper_generate",
            "newspaper_publish",
            "audio_generate",
        ]
        assert Path(audio_path).is_file()
        return {
            "status": "SENT",
            "edition_id": edition_id,
            "message_id": 789,
        }

    monkeypatch.setattr(
        production,
        "build_edition_newspaper",
        fake_build_newspaper,
    )
    monkeypatch.setattr(
        production,
        "generate_edition_audio",
        fake_generate_audio,
    )

    result = production.publish_edition(
        item,
        log=log,
        newspaper_publisher=fake_newspaper_publish,
        approval_manifest_path=approval_manifest,
        audio_publisher=fake_audio_publish,
    )

    assert result["status"] == COMPLETED
    assert result["newspaper_delivery"]["status"] == "SENT"
    assert result["audio"]["status"] == "GENERATED"
    assert result["audio_delivery"]["status"] == "SENT"
    assert calls == [
        "newspaper_generate",
        "newspaper_publish",
        "audio_generate",
        "audio_publish:114",
    ]

    log.close()


def test_publish_edition_does_not_regenerate_already_sent_audio(
    tmp_path,
    monkeypatch,
):
    from tests.conftest import create_approved_manifest
    import pipeline.edition_production as production

    item = edition()
    item["edition_number"] = 115

    log = SQLiteEditionDeliveryLog(":memory:")
    approval_manifest = create_approved_manifest(
        tmp_path,
        item["edition_id"],
    )

    log.record_sent(
        {"edition_id": item["edition_id"]},
        TELEGRAM_NEWSPAPER,
    )
    log.record_sent(
        {"edition_id": item["edition_id"]},
        TELEGRAM_AUDIO,
    )

    def unexpected_audio_generation(*args, **kwargs):
        raise AssertionError(
            "Audio generation must not run when Audio is already SENT"
        )

    monkeypatch.setattr(
        production,
        "generate_edition_audio",
        unexpected_audio_generation,
    )

    def unexpected_newspaper_publish(*args, **kwargs):
        raise AssertionError(
            "Newspaper delivery must not run when it is already SENT"
        )

    result = production.publish_edition(
        item,
        log=log,
        newspaper_publisher=unexpected_newspaper_publish,
        approval_manifest_path=approval_manifest,
    )

    assert result["status"] == COMPLETED
    assert result["newspaper"]["status"] == "SKIPPED"
    assert result["newspaper"]["reason"] == "ALREADY_SENT"
    assert result["audio"]["status"] == "SKIPPED"
    assert result["audio"]["reason"] == "ALREADY_SENT"

    log.close()
