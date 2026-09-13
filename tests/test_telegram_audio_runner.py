from pipeline.telegram_audio_runner import (
    publish_edition_audio_to_telegram,
)
from pipeline.edition_delivery_log import (
    TELEGRAM_AUDIO,
    SQLiteEditionDeliveryLog,
)


def test_audio_delivery_requires_approval(tmp_path):
    audio = tmp_path / "audio.ogg"
    audio.write_bytes(b"test")

    result = publish_edition_audio_to_telegram(
        "EDITION 0001",
        audio,
        approval_manifest_path=tmp_path / "manifest.json",
    )

    assert result["reason"] == "APPROVAL_NOT_APPROVED"


def test_audio_delivery_uses_transport(tmp_path):
    audio = tmp_path / "audio.ogg"
    audio.write_bytes(b"test")

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"edition_id": "EDITION 0001", "approval_status": "APPROVED"}',
        encoding="utf-8",
    )

    calls = []

    def transport(**kwargs):
        calls.append(kwargs)
        return {"ok": True, "result": {"message_id": 123}}

    log = SQLiteEditionDeliveryLog(":memory:")

    result = publish_edition_audio_to_telegram(
        "EDITION 0001",
        audio,
        approval_manifest_path=manifest,
        transport=transport,
        chat_id="@aroundthemain",
        log=log,
    )

    log.close()

    assert result["status"] == "SENT"
    assert result["message_id"] == 123
    assert calls[0]["chat_id"] == "@aroundthemain"

def test_audio_delivery_is_idempotent(tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"test")

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"edition_id": "EDITION 0114", "approval_status": "APPROVED"}',
        encoding="utf-8",
    )

    log = SQLiteEditionDeliveryLog(":memory:")
    calls = []

    def transport(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "result": {
                "message_id": 456,
            },
        }

    first = publish_edition_audio_to_telegram(
        "EDITION 0114",
        audio,
        edition_number=114,
        approval_manifest_path=manifest,
        transport=transport,
        chat_id="@aroundthemain",
        log=log,
    )

    second = publish_edition_audio_to_telegram(
        "EDITION 0114",
        audio,
        edition_number=114,
        approval_manifest_path=manifest,
        transport=transport,
        chat_id="@aroundthemain",
        log=log,
    )

    assert first["status"] == "SENT"
    assert second["status"] == "SKIPPED"
    assert second["reason"] == "ALREADY_SENT"

    assert len(calls) == 1
    assert log.has_been_sent(
        {"edition_id": "EDITION 0114"},
        TELEGRAM_AUDIO,
    )

    log.close()
