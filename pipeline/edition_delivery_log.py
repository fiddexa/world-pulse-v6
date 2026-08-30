"""
WORLD PULSE v6 - Edition Delivery Log

Persistent edition-level idempotency for channel delivery.

Event-level delivery remains handled by DeliveryLog.
This layer tracks the publication of a complete edition.
"""

import hashlib
import sqlite3
from pathlib import Path
from typing import Any


TELEGRAM = "telegram"

READY = "READY"
SENT = "SENT"
FAILED = "FAILED"


def edition_fingerprint(edition_publication: Any) -> str:
    """
    Return a deterministic fingerprint for an edition publication package.

    Edition ID is the primary identity. When no edition ID is available,
    the Telegram publication text is used as a deterministic fallback.
    """
    if not isinstance(edition_publication, dict):
        return ""

    edition_id = str(
        edition_publication.get("edition_id", "")
    ).strip()

    if edition_id:
        payload = f"edition:{edition_id}"
    else:
        telegram = edition_publication.get("telegram")

        if not isinstance(telegram, dict):
            return ""

        text = str(
            telegram.get("text", "")
        ).strip()

        if not text:
            return ""

        payload = f"telegram:{text}"

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


class SQLiteEditionDeliveryLog:
    """
    Persistent SQLite edition-level delivery log.
    """

    def __init__(
        self,
        db_path: str | Path = "data/edition_delivery.sqlite3",
    ):
        self.db_path = Path(db_path)

        if self.db_path.parent != Path("."):
            self.db_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(
            str(self.db_path)
        )

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS edition_delivery_records (
                fingerprint TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (fingerprint, channel)
            )
            """
        )

        self._connection.commit()

    @staticmethod
    def _valid_channel(channel: Any) -> bool:
        return channel == TELEGRAM

    def has_been_sent(
        self,
        edition_publication: Any,
        channel: Any,
    ) -> bool:
        fingerprint = edition_fingerprint(
            edition_publication
        )

        if not fingerprint or not self._valid_channel(channel):
            return False

        row = self._connection.execute(
            """
            SELECT status
            FROM edition_delivery_records
            WHERE fingerprint = ?
              AND channel = ?
            """,
            (
                fingerprint,
                channel,
            ),
        ).fetchone()

        return row is not None and row[0] == SENT

    def record_sent(
        self,
        edition_publication: Any,
        channel: Any,
    ) -> bool:
        fingerprint = edition_fingerprint(
            edition_publication
        )

        if not fingerprint or not self._valid_channel(channel):
            return False

        self._connection.execute(
            """
            INSERT INTO edition_delivery_records (
                fingerprint,
                channel,
                status
            )
            VALUES (?, ?, ?)
            ON CONFLICT(fingerprint, channel)
            DO UPDATE SET
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                fingerprint,
                channel,
                SENT,
            ),
        )

        self._connection.commit()

        return True

    def record_failed(
        self,
        edition_publication: Any,
        channel: Any,
    ) -> bool:
        fingerprint = edition_fingerprint(
            edition_publication
        )

        if not fingerprint or not self._valid_channel(channel):
            return False

        self._connection.execute(
            """
            INSERT INTO edition_delivery_records (
                fingerprint,
                channel,
                status
            )
            VALUES (?, ?, ?)
            ON CONFLICT(fingerprint, channel)
            DO UPDATE SET
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                fingerprint,
                channel,
                FAILED,
            ),
        )

        self._connection.commit()

        return True

    def status(
        self,
        edition_publication: Any,
        channel: Any,
    ) -> str | None:
        fingerprint = edition_fingerprint(
            edition_publication
        )

        if not fingerprint or not self._valid_channel(channel):
            return None

        row = self._connection.execute(
            """
            SELECT status
            FROM edition_delivery_records
            WHERE fingerprint = ?
              AND channel = ?
            """,
            (
                fingerprint,
                channel,
            ),
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def clear(self) -> None:
        self._connection.execute(
            "DELETE FROM edition_delivery_records"
        )

        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
