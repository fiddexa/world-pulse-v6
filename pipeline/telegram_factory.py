"""
WORLD PULSE v6 - Telegram Publisher Factory

Creates a production-ready TelegramPublisher from environment
configuration.

Secrets remain in environment variables and are never stored
in source code.
"""

from pipeline.telegram_config import telegram_configured
from pipeline.telegram_publisher import TelegramPublisher
from pipeline.telegram_transport import send_message_http


def get_telegram_publisher():
    """
    Return a configured TelegramPublisher.

    Returns None when Telegram configuration is incomplete.

    The real HTTP transport is injected explicitly so the publisher
    itself remains safe and fully testable.
    """

    if not telegram_configured():
        return None

    return TelegramPublisher(
        transport=send_message_http,
    )
