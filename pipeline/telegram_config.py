"""
AROUND THE MAIN v6 - Telegram Configuration

Reads Telegram configuration from environment variables.

Secrets must never be stored in source code or committed to Git.
"""

import os


TELEGRAM_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV = "TELEGRAM_CHAT_ID"


def get_telegram_bot_token():
    """Return the Telegram bot token from the environment."""
    value = os.getenv(TELEGRAM_BOT_TOKEN_ENV, "")
    return value.strip()


def get_telegram_chat_id():
    """Return the Telegram destination chat ID from the environment."""
    value = os.getenv(TELEGRAM_CHAT_ID_ENV, "")
    return value.strip()


def telegram_configured():
    """
    Return True only when both required Telegram values exist.
    """
    return bool(
        get_telegram_bot_token()
        and get_telegram_chat_id()
    )
