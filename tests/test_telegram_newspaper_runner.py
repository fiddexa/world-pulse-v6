from pathlib import Path

from pipeline.edition_delivery_log import (
    TELEGRAM_NEWSPAPER,
    SQLiteEditionDeliveryLog,
)
from pipeline.telegram_newspaper_runner import (
    newspaper_delivery_already_sent,
    publish_edition_newspaper_to_telegram,
)


def approved_manifest(tmp_path, edition_id):
    from tests.conftest import create_approved_manifest

    return create_approved_manifest(
        tmp_path,
        edition_id,
    )


def test_newspaper_delivery_sends_all_pages_and_records_sent(tmp_path):
    edition_id = "AROUND-THE-MAIN-EN-2026-09-13-2000"
    manifest = approved_manifest(tmp_path, edition_id)
    log = SQLiteEditionDeliveryLog(":memory:")

    pages = []
    for number in (1, 2, 3):
        path = tmp_path / f"page-{number:02d}.png"
        path.write_bytes(b"png")
        pages.append(path)

    calls = []

    def transport(*, chat_id, photo_path, caption):
        calls.append((chat_id, photo_path, caption))
        return {
            "ok": True,
            "result": {"message_id": 100 + len(calls)},
        }

    result = publish_edition_newspaper_to_telegram(
        edition_id,
        pages,
        edition_number=122,
        approval_manifest_path=manifest,
        transport=transport,
        chat_id="@aroundthemain",
        log=log,
    )

    assert result["status"] == "SENT"
    assert result["pages_total"] == 3
    assert result["message_ids"] == [101, 102, 103]
    assert len(calls) == 3
    assert calls[0][0] == "@aroundthemain"
    assert calls[0][2] == ""
    assert calls[1][2] == ""
    assert log.has_been_sent(
        {"edition_id": edition_id},
        TELEGRAM_NEWSPAPER,
    )
    assert newspaper_delivery_already_sent(
        edition_id,
        log=log,
    )

    log.close()


def test_newspaper_delivery_skips_already_sent(tmp_path):
    edition_id = "AROUND-THE-MAIN-EN-2026-09-13-2001"
    manifest = approved_manifest(tmp_path, edition_id)
    log = SQLiteEditionDeliveryLog(":memory:")
    log.record_sent(
        {"edition_id": edition_id},
        TELEGRAM_NEWSPAPER,
    )

    page = tmp_path / "page-01.png"
    page.write_bytes(b"png")

    calls = []

    def transport(**kwargs):
        calls.append(kwargs)
        return {"ok": True, "result": {"message_id": 1}}

    result = publish_edition_newspaper_to_telegram(
        edition_id,
        [page],
        edition_number=123,
        approval_manifest_path=manifest,
        transport=transport,
        chat_id="@aroundthemain",
        log=log,
    )

    assert result["status"] == "SKIPPED"
    assert result["reason"] == "ALREADY_SENT"
    assert calls == []

    log.close()


def test_newspaper_delivery_fails_without_pages(tmp_path):
    edition_id = "AROUND-THE-MAIN-EN-2026-09-13-2002"
    manifest = approved_manifest(tmp_path, edition_id)
    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition_newspaper_to_telegram(
        edition_id,
        [],
        edition_number=124,
        approval_manifest_path=manifest,
        transport=lambda **kwargs: {"ok": True},
        chat_id="@aroundthemain",
        log=log,
    )

    assert result["status"] == "FAILED"
    assert result["reason"] == "NO_NEWSPAPER_PAGES"

    log.close()
