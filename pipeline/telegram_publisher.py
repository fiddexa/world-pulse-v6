"""
AROUND THE MAIN v6 - Telegram Publisher

Publishes prepared Telegram content through the Telegram Bot API.

The token and chat ID are read only from environment variables.
The transport is injectable so all behavior can be tested without
making real network requests.
"""

import json
from typing import Any, Callable

from pipeline.publisher import Publisher, TELEGRAM
from pipeline.telegram_config import (
    get_telegram_bot_token,
    get_telegram_chat_id,
)


class TelegramPublisher(Publisher):
    """
    Telegram Bot API publisher.

    `transport` is an injectable callable used by tests.
    A real HTTP transport is intentionally not included yet.
    """

    channel = TELEGRAM

    def __init__(
        self,
        *,
        token: str | None = None,
        chat_id: str | None = None,
        transport: Callable[..., Any] | None = None,
    ):
        self.token = (
            token
            if token is not None
            else get_telegram_bot_token()
        ).strip()

        self.chat_id = (
            chat_id
            if chat_id is not None
            else get_telegram_chat_id()
        ).strip()

        self.transport = transport

    def configured(self) -> bool:
        return bool(
            self.token
            and self.chat_id
        )

    def _message_text(self, event: dict) -> str:
        publication = event.get("publication")

        if not isinstance(publication, dict):
            return ""

        value = publication.get("telegram")

        if value is None:
            return ""

        return str(value).strip()

    def publish(self, event: dict) -> dict:
        """
        Publish one prepared event.

        No external request is made when no transport has been
        provided. In that case the publisher returns NOT_CONFIGURED.
        """

        if not isinstance(event, dict):
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "INVALID_EVENT",
            }

        if not self.configured():
            return {
                "status": "NOT_CONFIGURED",
                "channel": TELEGRAM,
            }

        text = self._message_text(event)

        if not text:
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "NO_CONTENT",
            }

        if self.transport is None:
            return {
                "status": "NOT_CONFIGURED",
                "channel": TELEGRAM,
            }

        payload = {
            "chat_id": self.chat_id,
            "text": text,
        }

        try:
            response = self.transport(
                token=self.token,
                payload=payload,
            )
        except Exception as exc:
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "TRANSPORT_ERROR",
                "error": str(exc),
            }

        if not isinstance(response, dict):
            return {
                "status": "FAILED",
                "channel": TELEGRAM,
                "reason": "INVALID_RESPONSE",
            }

        if response.get("ok") is True:
            return {
                "status": "SENT",
                "channel": TELEGRAM,
                "message_id": response.get(
                    "result",
                    {},
                ).get("message_id")
                if isinstance(response.get("result"), dict)
                else None,
            }

        return {
            "status": "FAILED",
            "channel": TELEGRAM,
            "reason": "TELEGRAM_API_ERROR",
            "response": response,
        }


def json_transport_from_response(raw_response: str):
    """
    Small helper for deterministic tests and adapters.
    """

    def transport(**kwargs):
        return json.loads(raw_response)

    return transport
