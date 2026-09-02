"""
AROUND THE MAIN v6 - Delivery Log

Provides deterministic event fingerprints and in-memory delivery
state for idempotent publishing decisions.

This layer does not publish externally.
"""

import hashlib
import json
from typing import Any


TELEGRAM = "telegram"
WEBSITE = "website"

READY = "READY"
SENT = "SENT"
FAILED = "FAILED"


def _canonical_payload(event: Any) -> str:
    """
    Build a stable JSON representation of the event's publication
    identity.

    Only publication-relevant stable fields are included.
    """

    if not isinstance(event, dict):
        return ""

    content = event.get("content")

    if not isinstance(content, dict):
        content = {}

    payload = {
        "headline": content.get("headline", ""),
        "published_at": content.get("published_at", ""),
        "sources": content.get("sources", []),
        "affected_areas": content.get("affected_areas", []),
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def event_fingerprint(event: Any) -> str:
    """
    Return a deterministic SHA-256 fingerprint for an event.
    """

    payload = _canonical_payload(event)

    if not payload:
        return ""

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def _valid_channel(channel: Any) -> bool:
    return channel in {
        TELEGRAM,
        WEBSITE,
    }


def create_delivery_record(event: Any, channel: Any) -> dict:
    """
    Create a delivery record without mutating the event.
    """

    fingerprint = event_fingerprint(event)

    if not fingerprint or not _valid_channel(channel):
        return {
            "fingerprint": fingerprint,
            "channel": channel,
            "status": FAILED,
        }

    return {
        "fingerprint": fingerprint,
        "channel": channel,
        "status": READY,
    }


class DeliveryLog:
    """
    Simple in-memory delivery log.

    Designed as the first implementation of the idempotency layer.
    It can later be replaced by SQLite or another persistent store
    without changing the public API.
    """

    def __init__(self):
        self._records = {}

    def has_been_sent(self, event: Any, channel: Any) -> bool:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not _valid_channel(channel):
            return False

        return self._records.get(
            (fingerprint, channel)
        ) == SENT

    def record_sent(self, event: Any, channel: Any) -> bool:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not _valid_channel(channel):
            return False

        self._records[
            (fingerprint, channel)
        ] = SENT

        return True

    def record_failed(self, event: Any, channel: Any) -> bool:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not _valid_channel(channel):
            return False

        self._records[
            (fingerprint, channel)
        ] = FAILED

        return True

    def status(self, event: Any, channel: Any) -> str | None:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not _valid_channel(channel):
            return None

        return self._records.get(
            (fingerprint, channel)
        )

    def clear(self) -> None:
        self._records.clear()
