"""
WORLD PULSE v6 - SQLite Delivery Log

Persistent delivery state for idempotent publishing decisions.

This layer stores delivery state in SQLite so that delivery
information survives process restarts.
"""

import sqlite3
from pathlib import Path
from typing import Any

from pipeline.delivery_log import (
    FAILED,
    SENT,
    TELEGRAM,
    WEBSITE,
    event_fingerprint,
)


class SQLiteDeliveryLog:
    """
    Persistent SQLite implementation of the delivery log.

    Public behavior intentionally mirrors DeliveryLog so it can
    later be injected into the existing delivery/orchestration layer.
    """

    def __init__(self, db_path: str | Path = "data/delivery.sqlite3"):
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
            CREATE TABLE IF NOT EXISTS delivery_records (
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
        return channel in {
            TELEGRAM,
            WEBSITE,
        }

    def has_been_sent(
        self,
        event: Any,
        channel: Any,
    ) -> bool:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not self._valid_channel(channel):
            return False

        row = self._connection.execute(
            """
            SELECT status
            FROM delivery_records
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
        event: Any,
        channel: Any,
    ) -> bool:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not self._valid_channel(channel):
            return False

        self._connection.execute(
            """
            INSERT INTO delivery_records (
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
        event: Any,
        channel: Any,
    ) -> bool:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not self._valid_channel(channel):
            return False

        self._connection.execute(
            """
            INSERT INTO delivery_records (
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
        event: Any,
        channel: Any,
    ) -> str | None:
        fingerprint = event_fingerprint(event)

        if not fingerprint or not self._valid_channel(channel):
            return None

        row = self._connection.execute(
            """
            SELECT status
            FROM delivery_records
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
            "DELETE FROM delivery_records"
        )

        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
