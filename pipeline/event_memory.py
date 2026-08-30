"""
WORLD PULSE v6 - Persistent Event Memory

Stores deterministic event memory in SQLite.

Event identity is based on the existing event_fingerprint()
from pipeline.delivery_log so the project has one canonical
event identity mechanism.
"""

import sqlite3
from pathlib import Path
from typing import Any

from pipeline.delivery_log import event_fingerprint


class EventMemory:
    """
    Persistent SQLite memory for previously observed events.

    The memory tracks:
    - first_seen;
    - last_seen;
    - occurrence_count;
    - last_edition_id.

    Event identity is the existing SHA-256 event fingerprint.
    """

    def __init__(
        self,
        db_path: str | Path = "data/event_memory.sqlite3",
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
            CREATE TABLE IF NOT EXISTS event_memory (
                fingerprint TEXT PRIMARY KEY,
                first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER NOT NULL DEFAULT 1,
                last_edition_id TEXT
            )
            """
        )

        self._connection.commit()

    def remember(
        self,
        event: Any,
        edition_id: str | None = None,
    ) -> bool:
        """
        Remember an event.

        A new event is inserted with occurrence_count=1.
        An existing event updates last_seen and increments
        occurrence_count.
        """

        fingerprint = event_fingerprint(event)

        if not fingerprint:
            return False

        self._connection.execute(
            """
            INSERT INTO event_memory (
                fingerprint,
                first_seen,
                last_seen,
                occurrence_count,
                last_edition_id
            )
            VALUES (
                ?,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                1,
                ?
            )
            ON CONFLICT(fingerprint)
            DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                occurrence_count =
                    event_memory.occurrence_count + 1,
                last_edition_id =
                    COALESCE(
                        excluded.last_edition_id,
                        event_memory.last_edition_id
                    )
            """,
            (
                fingerprint,
                edition_id,
            ),
        )

        self._connection.commit()

        return True

    def has_seen(self, event: Any) -> bool:
        """
        Return True when the event exists in memory.
        """

        fingerprint = event_fingerprint(event)

        if not fingerprint:
            return False

        row = self._connection.execute(
            """
            SELECT 1
            FROM event_memory
            WHERE fingerprint = ?
            """,
            (fingerprint,),
        ).fetchone()

        return row is not None

    def get(self, event: Any) -> dict | None:
        """
        Return stored memory information for an event.
        """

        fingerprint = event_fingerprint(event)

        if not fingerprint:
            return None

        row = self._connection.execute(
            """
            SELECT
                fingerprint,
                first_seen,
                last_seen,
                occurrence_count,
                last_edition_id
            FROM event_memory
            WHERE fingerprint = ?
            """,
            (fingerprint,),
        ).fetchone()

        if row is None:
            return None

        return {
            "fingerprint": row[0],
            "first_seen": row[1],
            "last_seen": row[2],
            "occurrence_count": row[3],
            "last_edition_id": row[4],
        }

    def forget(self, event: Any) -> bool:
        """
        Remove an event from memory.
        """

        fingerprint = event_fingerprint(event)

        if not fingerprint:
            return False

        cursor = self._connection.execute(
            """
            DELETE FROM event_memory
            WHERE fingerprint = ?
            """,
            (fingerprint,),
        )

        self._connection.commit()

        return cursor.rowcount > 0

    def clear(self) -> None:
        """
        Remove all stored events.
        """

        self._connection.execute(
            "DELETE FROM event_memory"
        )

        self._connection.commit()

    def close(self) -> None:
        """
        Close the SQLite connection.
        """

        self._connection.close()
