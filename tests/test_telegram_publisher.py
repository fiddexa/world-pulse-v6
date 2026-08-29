from pipeline.telegram_publisher import (
    TelegramPublisher,
    json_transport_from_response,
)
from pipeline.publisher import TELEGRAM


def event():
    return {
        "publication": {
            "telegram": (
                "Major earthquake strikes Nepal"
            )
        }
    }


def test_publisher_channel_is_telegram():
    publisher = TelegramPublisher()

    assert publisher.channel == TELEGRAM


def test_publisher_is_not_configured_without_credentials(
    monkeypatch,
):
    monkeypatch.delenv(
        "TELEGRAM_BOT_TOKEN",
        raising=False,
    )
    monkeypatch.delenv(
        "TELEGRAM_CHAT_ID",
        raising=False,
    )

    publisher = TelegramPublisher()

    assert publisher.configured() is False


def test_publisher_uses_explicit_credentials():
    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
    )

    assert publisher.configured() is True


def test_missing_transport_does_not_make_real_request():
    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
    )

    result = publisher.publish(event())

    assert result["status"] == "NOT_CONFIGURED"


def test_invalid_event_is_rejected():
    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
    )

    result = publisher.publish(None)

    assert result["status"] == "FAILED"
    assert result["reason"] == "INVALID_EVENT"


def test_missing_telegram_content_is_rejected():
    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
    )

    result = publisher.publish(
        {"publication": {}}
    )

    assert result["status"] == "FAILED"
    assert result["reason"] == "NO_CONTENT"


def test_successful_transport_sends_expected_payload():
    calls = []

    def transport(**kwargs):
        calls.append(kwargs)

        return {
            "ok": True,
            "result": {
                "message_id": 42,
            },
        }

    publisher = TelegramPublisher(
        token="secret-token",
        chat_id="-100123",
        transport=transport,
    )

    result = publisher.publish(event())

    assert result["status"] == "SENT"
    assert result["message_id"] == 42

    assert calls[0]["token"] == "secret-token"
    assert calls[0]["payload"]["chat_id"] == "-100123"
    assert calls[0]["payload"]["text"] == (
        "Major earthquake strikes Nepal"
    )


def test_api_error_is_reported():
    def transport(**kwargs):
        return {
            "ok": False,
            "error_code": 400,
            "description": "Bad Request",
        }

    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
        transport=transport,
    )

    result = publisher.publish(event())

    assert result["status"] == "FAILED"
    assert result["reason"] == "TELEGRAM_API_ERROR"


def test_transport_exception_is_reported():
    def transport(**kwargs):
        raise RuntimeError("network failed")

    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
        transport=transport,
    )

    result = publisher.publish(event())

    assert result["status"] == "FAILED"
    assert result["reason"] == "TRANSPORT_ERROR"


def test_invalid_transport_response_is_reported():
    def transport(**kwargs):
        return "invalid"

    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
        transport=transport,
    )

    result = publisher.publish(event())

    assert result["status"] == "FAILED"
    assert result["reason"] == "INVALID_RESPONSE"


def test_json_transport_helper():
    transport = json_transport_from_response(
        '{"ok": true, "result": {"message_id": 7}}'
    )

    response = transport(
        token="token",
        payload={},
    )

    assert response["ok"] is True
    assert response["result"]["message_id"] == 7


def test_publisher_does_not_modify_event():
    original = event()
    before = {
        "publication": dict(
            original["publication"]
        )
    }

    def transport(**kwargs):
        return {
            "ok": True,
            "result": {
                "message_id": 1,
            },
        }

    publisher = TelegramPublisher(
        token="token",
        chat_id="-100123",
        transport=transport,
    )

    publisher.publish(original)

    assert original == before
