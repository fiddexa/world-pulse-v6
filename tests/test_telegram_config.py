from pipeline.telegram_config import (
    TELEGRAM_BOT_TOKEN_ENV,
    TELEGRAM_CHAT_ID_ENV,
    get_telegram_bot_token,
    get_telegram_chat_id,
    telegram_configured,
)


def test_missing_token_returns_empty(monkeypatch):
    monkeypatch.delenv(
        TELEGRAM_BOT_TOKEN_ENV,
        raising=False,
    )

    assert get_telegram_bot_token() == ""


def test_missing_chat_id_returns_empty(monkeypatch):
    monkeypatch.delenv(
        TELEGRAM_CHAT_ID_ENV,
        raising=False,
    )

    assert get_telegram_chat_id() == ""


def test_token_is_read_from_environment(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        " test-token ",
    )

    assert get_telegram_bot_token() == "test-token"


def test_chat_id_is_read_from_environment(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_CHAT_ID_ENV,
        " -1001234567890 ",
    )

    assert get_telegram_chat_id() == "-1001234567890"


def test_configuration_requires_both_values(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        "token",
    )
    monkeypatch.delenv(
        TELEGRAM_CHAT_ID_ENV,
        raising=False,
    )

    assert telegram_configured() is False


def test_configuration_is_ready(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        "token",
    )
    monkeypatch.setenv(
        TELEGRAM_CHAT_ID_ENV,
        "-1001234567890",
    )

    assert telegram_configured() is True


def test_empty_token_is_not_configured(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        "",
    )
    monkeypatch.setenv(
        TELEGRAM_CHAT_ID_ENV,
        "-1001234567890",
    )

    assert telegram_configured() is False


def test_whitespace_values_are_not_configured(monkeypatch):
    monkeypatch.setenv(
        TELEGRAM_BOT_TOKEN_ENV,
        "   ",
    )
    monkeypatch.setenv(
        TELEGRAM_CHAT_ID_ENV,
        "   ",
    )

    assert telegram_configured() is False
