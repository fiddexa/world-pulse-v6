from pipeline.telegram_factory import (
    get_telegram_publisher,
)
from pipeline.telegram_publisher import TelegramPublisher
from pipeline.telegram_config import (
    TELEGRAM_BOT_TOKEN_ENV,
    TELEGRAM_CHAT_ID_ENV,
)


def test_factory_returns_none_when_not_configured(monkeypatch):
    monkeypatch.delenv(
        TELEGRAM_BOT_TOKEN_ENV,
        raising=False,
    )
    monkeypatch.delenv(
        TELEGRAM_CHAT_ID_ENV,
        raising=False,
    )

    assert get_telegram_publisher() is None


def test_factory_returns_publisher_when_configured(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        "test-token",
    )
    monkeypatch.setenv(
        TELEGRAM_CHAT_ID_ENV,
        "-100123456789",
    )

    publisher = get_telegram_publisher()

    assert isinstance(
        publisher,
        TelegramPublisher,
    )

    assert publisher.configured() is True


def test_factory_injects_http_transport(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        "test-token",
    )
    monkeypatch.setenv(
        TELEGRAM_CHAT_ID_ENV,
        "-100123456789",
    )

    publisher = get_telegram_publisher()

    assert publisher.transport is not None
    assert publisher.transport.__name__ == (
        "send_message_http"
    )
