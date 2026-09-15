"""
AROUND THE MAIN v6 - Market Data

Fetches a fresh market snapshot for each edition.

The module is intentionally independent from rendering and Telegram
delivery. A snapshot can be stored inside an edition archive and then
consumed by any publication format later.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MARKET_API_URL = "https://biquote.io/api/latest"
MARKET_PROVIDER = "BiQuote"

# Minimum business-world market set currently verified against the
# live BiQuote endpoint.
MARKET_SYMBOLS = {
    "sp500": "US500",
    "dow": "US30",
    "brent": "UKOIL",
    "wti": "USOIL",
    "gold": "XAUUSD",
    "eur_usd": "EURUSD",
    "usd_cny": "USDCNH",
    "dxy": "DXY",
}

MAX_OPEN_QUOTE_AGE_SECONDS = 300


class MarketDataError(RuntimeError):
    """Raised when a usable market snapshot cannot be built."""


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _request_url(symbols: list[str]) -> str:
    query = urlencode(
        [("symbols", symbol) for symbol in symbols]
    )
    return f"{MARKET_API_URL}?{query}"


def _fetch_json(
    symbols: list[str],
    *,
    timeout: int = 15,
) -> dict[str, Any]:
    url = _request_url(symbols)

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; AROUND-THE-MAIN/1.0)"
            )
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")

    except Exception as exc:
        raise MarketDataError(
            f"Market data request failed: {exc}"
        ) from exc

    try:
        data = json.loads(payload)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MarketDataError(
            "Market data response is not valid JSON"
        ) from exc

    if not isinstance(data, dict):
        raise MarketDataError(
            "Market data response must be a JSON object"
        )

    return data


def _normalise_quote(
    *,
    key: str,
    symbol: str,
    payload: dict[str, Any],
    fetched_at: datetime,
) -> dict[str, Any]:
    item = payload.get(symbol)

    if not isinstance(item, dict):
        raise MarketDataError(
            f"Missing market data for {symbol}"
        )

    mid = item.get("mid")

    if not isinstance(mid, (int, float)):
        raise MarketDataError(
            f"Invalid mid price for {symbol}"
        )

    timestamp = item.get("timestamp")
    market_state = str(
        item.get("marketState") or ""
    ).strip().lower()

    stale = bool(item.get("stale", False))
    quote_age = item.get("quoteAgeSeconds")

    if not isinstance(quote_age, (int, float)):
        quote_age = None

    # For open markets we require a genuinely fresh quote.
    if market_state == "open":
        if stale:
            raise MarketDataError(
                f"Stale open-market quote for {symbol}"
            )

        if (
            quote_age is None
            or quote_age > MAX_OPEN_QUOTE_AGE_SECONDS
        ):
            raise MarketDataError(
                f"Open-market quote too old for {symbol}: "
                f"{quote_age}"
            )

    return {
        "key": key,
        "symbol": symbol,
        "value": float(mid),
        "change_pct": (
            float(item["dayDiffPercent"])
            if isinstance(
                item.get("dayDiffPercent"),
                (int, float),
            )
            else None
        ),
        "timestamp": timestamp,
        "fetched_at": fetched_at.isoformat(),
        "market_state": market_state or None,
        "stale": stale,
        "quote_age_seconds": (
            float(quote_age)
            if quote_age is not None
            else None
        ),
        "source": str(
            item.get("source") or MARKET_PROVIDER
        ),
    }


def fetch_market_snapshot(
    *,
    timeout: int = 15,
    fetched_at: datetime | None = None,
) -> dict[str, Any]:
    """
    Fetch one fresh market snapshot.

    A new network request is made every time this function is called.

    The returned snapshot is deliberately renderer-independent.
    """
    fetched_at = (
        fetched_at
        if fetched_at is not None
        else _now_utc()
    )

    symbols = list(
        MARKET_SYMBOLS.values()
    )

    payload = _fetch_json(
        symbols,
        timeout=timeout,
    )

    quotes: dict[str, dict[str, Any]] = {}

    for key, symbol in MARKET_SYMBOLS.items():
        quotes[key] = _normalise_quote(
            key=key,
            symbol=symbol,
            payload=payload,
            fetched_at=fetched_at,
        )

    return {
        "provider": MARKET_PROVIDER,
        "fetched_at": fetched_at.isoformat(),
        "quotes": quotes,
    }
