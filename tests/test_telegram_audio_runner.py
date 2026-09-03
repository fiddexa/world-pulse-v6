from pipeline.telegram_audio_runner import (
    publish_edition_audio_to_telegram,
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

    result = publish_edition_audio_to_telegram(
        "EDITION 0001",
        audio,
        approval_manifest_path=manifest,
        transport=transport,
        chat_id="@aroundthemain",
    )

    assert result["status"] == "SENT"
    assert result["message_id"] == 123
    assert calls[0]["chat_id"] == "@aroundthemain"
