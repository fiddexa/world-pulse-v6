from datetime import datetime, timezone
import json

import pytest

from pipeline.market_data import (
    MarketDataError,
    fetch_market_snapshot,
)


def _payload():
    return {
        "US500": {
            "mid": 7587.68,
            "dayDiffPercent": -0.439,
            "timestamp": "2026-09-15T09:08:32Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 2,
            "marketState": "open",
        },
        "US30": {
            "mid": 52084.05,
            "dayDiffPercent": -0.677,
            "timestamp": "2026-09-15T09:08:31Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 1,
            "marketState": "open",
        },
        "UKOIL": {
            "mid": 104.346,
            "dayDiffPercent": 2.5508,
            "timestamp": "2026-09-15T09:08:31Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 1,
            "marketState": "open",
        },
        "USOIL": {
            "mid": 91.71,
            "dayDiffPercent": 1.01,
            "timestamp": "2026-09-15T09:08:31Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 1,
            "marketState": "open",
        },
        "XAUUSD": {
            "mid": 4266.207,
            "dayDiffPercent": -0.5164,
            "timestamp": "2026-09-15T09:08:31Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 1,
            "marketState": "open",
        },
        "EURUSD": {
            "mid": 1.15352,
            "dayDiffPercent": -0.5037,
            "timestamp": "2026-09-15T09:08:31Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 1,
            "marketState": "open",
        },
        "USDCNH": {
            "mid": 6.714155,
            "dayDiffPercent": 0.0995,
            "timestamp": "2026-09-15T09:08:32Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 0,
            "marketState": "open",
        },
        "DXY": {
            "mid": 99.6365,
            "dayDiffPercent": 0.5317,
            "timestamp": "2026-09-15T09:08:30Z",
            "source": "Test Provider",
            "stale": False,
            "quoteAgeSeconds": 2,
            "marketState": "open",
        },
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False

    def read(self):
        return json.dumps(
            self.payload
        ).encode("utf-8")


def test_fetch_market_snapshot_returns_all_verified_quotes(
    monkeypatch,
):
    def fake_urlopen(request, timeout=15):
        return FakeResponse(_payload())

    monkeypatch.setattr(
        "pipeline.market_data.urlopen",
        fake_urlopen,
    )

    fetched_at = datetime(
        2026,
        9,
        15,
        9,
        10,
        0,
        tzinfo=timezone.utc,
    )

    result = fetch_market_snapshot(
        fetched_at=fetched_at,
    )

    assert result["provider"] == "BiQuote"
    assert result["fetched_at"] == (
        "2026-09-15T09:10:00+00:00"
    )

    quotes = result["quotes"]

    assert len(quotes) == 8
    assert quotes["sp500"]["value"] == 7587.68
    assert quotes["dow"]["change_pct"] == -0.677
    assert quotes["gold"]["quote_age_seconds"] == 1
    assert quotes["eur_usd"]["symbol"] == "EURUSD"
    assert quotes["dxy"]["stale"] is False


def test_fetch_market_snapshot_rejects_stale_open_quote(
    monkeypatch,
):
    payload = _payload()
    payload["US500"]["stale"] = True

    def fake_urlopen(request, timeout=15):
        return FakeResponse(payload)

    monkeypatch.setattr(
        "pipeline.market_data.urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        MarketDataError,
        match="Stale open-market quote",
    ):
        fetch_market_snapshot()


def test_fetch_market_snapshot_rejects_old_open_quote(
    monkeypatch,
):
    payload = _payload()
    payload["US30"]["quoteAgeSeconds"] = 301

    def fake_urlopen(request, timeout=15):
        return FakeResponse(payload)

    monkeypatch.setattr(
        "pipeline.market_data.urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        MarketDataError,
        match="Open-market quote too old",
    ):
        fetch_market_snapshot()


def test_fetch_market_snapshot_accepts_last_quote_when_market_is_closed(
    monkeypatch,
):
    payload = _payload()
    payload["US500"]["marketState"] = "closed"
    payload["US500"]["quoteAgeSeconds"] = 14400

    def fake_urlopen(request, timeout=15):
        return FakeResponse(payload)

    monkeypatch.setattr(
        "pipeline.market_data.urlopen",
        fake_urlopen,
    )

    result = fetch_market_snapshot()

    assert result["quotes"]["sp500"]["market_state"] == "closed"
    assert result["quotes"]["sp500"]["value"] == 7587.68
    assert result["quotes"]["sp500"]["quote_age_seconds"] == 14400
