"""
AROUND THE MAIN v6 - Telegram HTTP Transport

Small transport adapter for Telegram Bot API.

No credentials are stored here.
The bot token is supplied by TelegramPublisher.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TELEGRAM_API_BASE = "https://api.telegram.org"


def send_message_http(
    *,
    token: str,
    payload: dict,
    timeout: float = 15.0,
):
    """
    Send a Telegram Bot API sendMessage request.

    Returns the decoded Telegram JSON response.

    Raises:
        ValueError: invalid arguments.
        HTTPError: HTTP-level failure.
        URLError: network-level failure.
        TimeoutError: request timeout.
    """

    if not token or not str(token).strip():
        raise ValueError("Telegram token is required")

    if not isinstance(payload, dict):
        raise ValueError("Telegram payload must be a dictionary")

    url = (
        f"{TELEGRAM_API_BASE}/bot"
        f"{str(token).strip()}/sendMessage"
    )

    body = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=timeout,
        ) as response:
            raw = response.read().decode("utf-8")

    except TimeoutError:
        raise

    if not raw:
        raise ValueError(
            "Telegram returned an empty response"
        )

    return json.loads(raw)
