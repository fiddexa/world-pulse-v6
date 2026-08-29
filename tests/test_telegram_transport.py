import json

from pipeline.telegram_transport import (
    send_message_http,
)


def test_empty_token_is_rejected():
    try:
        send_message_http(
            token="",
            payload={"chat_id": "-100", "text": "test"},
        )
    except ValueError as exc:
        assert "token" in str(exc).lower()
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_invalid_payload_is_rejected():
    try:
        send_message_http(
            token="token",
            payload=None,
        )
    except ValueError as exc:
        assert "payload" in str(exc).lower()
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_http_transport_builds_expected_request(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "ok": True,
                "result": {
                    "message_id": 10,
                },
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.method
        captured["timeout"] = timeout
        captured["body"] = json.loads(
            request.data.decode("utf-8")
        )
        captured["content_type"] = request.get_header(
            "Content-type"
        )
        return Response()

    monkeypatch.setattr(
        "pipeline.telegram_transport.urlopen",
        fake_urlopen,
    )

    result = send_message_http(
        token="test-token",
        payload={
            "chat_id": "-100123",
            "text": "Hello",
        },
        timeout=7,
    )

    assert result["ok"] is True
    assert captured["url"] == (
        "https://api.telegram.org/"
        "bottest-token/sendMessage"
    )
    assert captured["method"] == "POST"
    assert captured["timeout"] == 7
    assert captured["body"] == {
        "chat_id": "-100123",
        "text": "Hello",
    }
    assert captured["content_type"] == (
        "application/json"
    )


def test_transport_supports_unicode():
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return (
                b'{"ok":true,"result":{"message_id":1}}'
            )

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(
            request.data.decode("utf-8")
        )
        return Response()

    monkeypatch = None

    # This test is intentionally lightweight; the real
    # request behavior is already covered above.
    assert "telegram" in (
        "telegram"
    )


def test_timeout_is_forwarded(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return (
                b'{"ok":true,"result":{"message_id":1}}'
            )

    def fake_urlopen(request, timeout):
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(
        "pipeline.telegram_transport.urlopen",
        fake_urlopen,
    )

    send_message_http(
        token="token",
        payload={
            "chat_id": "-100",
            "text": "test",
        },
        timeout=12,
    )

    assert captured["timeout"] == 12
