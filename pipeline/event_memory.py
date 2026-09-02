"""
AROUND THE MAIN v6 - Persistent Event Memory

Stores deterministic event memory and edition history in SQLite.

Event identity is based on the existing event_fingerprint()
from pipeline.delivery_log so the project has one canonical
event identity mechanism.
"""

import sqlite3
from pathlib import Path
from typing import Any

from pipeline.delivery_log import event_fingerprint
from pipeline.edition_id import build_edition_id


class EventMemory:
    """
    Persistent SQLite memory for previously observed events.

    The memory tracks:
    - first_seen;
    - last_seen;
    - occurrence_count;
    - last_edition_id.

    A separate history table records every edition in which
    an event was explicitly marked as used.
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

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS event_edition_history (
                fingerprint TEXT NOT NULL,
                edition_id TEXT NOT NULL,
                used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (fingerprint, edition_id)
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
        Remember that an event was observed.

        A new event is inserted with occurrence_count=1.
        An existing event updates last_seen and increments
        occurrence_count.

        If edition_id is supplied, the event is also recorded
        as used by that edition.
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

        if edition_id is not None:
            if not self._valid_edition_id(edition_id):
                self._connection.rollback()
                return False

            self._connection.execute(
                """
                INSERT OR IGNORE INTO event_edition_history (
                    fingerprint,
                    edition_id
                )
                VALUES (?, ?)
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

    def edition_history(self, event: Any) -> list[str]:
        """
        Return edition IDs in which the event was explicitly used.
        """

        fingerprint = event_fingerprint(event)

        if not fingerprint:
            return []

        rows = self._connection.execute(
            """
            SELECT edition_id
            FROM event_edition_history
            WHERE fingerprint = ?
            ORDER BY used_at ASC, edition_id ASC
            """,
            (fingerprint,),
        ).fetchall()

        return [row[0] for row in rows]

    def used_in_edition(
        self,
        event: Any,
        edition_id: str,
    ) -> bool:
        """
        Return True when an event was explicitly used in an edition.
        """

        fingerprint = event_fingerprint(event)

        if not fingerprint or not self._valid_edition_id(edition_id):
            return False

        row = self._connection.execute(
            """
            SELECT 1
            FROM event_edition_history
            WHERE fingerprint = ?
              AND edition_id = ?
            """,
            (
                fingerprint,
                edition_id,
            ),
        ).fetchone()

        return row is not None

    def forget(self, event: Any) -> bool:
        """
        Remove an event and its edition history from memory.
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

        self._connection.execute(
            """
            DELETE FROM event_edition_history
            WHERE fingerprint = ?
            """,
            (fingerprint,),
        )

        self._connection.commit()

        return cursor.rowcount > 0

    def clear(self) -> None:
        """
        Remove all stored events and edition history.
        """

        self._connection.execute(
            "DELETE FROM event_edition_history"
        )

        self._connection.execute(
            "DELETE FROM event_memory"
        )

        self._connection.commit()

    def close(self) -> None:
        """
        Close the SQLite connection.
        """

        self._connection.close()

    @staticmethod
    def _valid_edition_id(edition_id: Any) -> bool:
        """
        Validate the stable Edition ID format.

        The ID is validated by parsing its canonical components.
        """

        if not isinstance(edition_id, str):
            return False

        parts = edition_id.split("-")

        if len(parts) != 8:
            return False

        if (
            parts[0] != "AROUND"
            or parts[1] != "THE"
            or parts[2] != "MAIN"
        ):
            return False

        language = parts[3]
        publication_date = "-".join(parts[4:7])
        edition_time_raw = parts[7]

        if len(edition_time_raw) != 4:
            return False

        edition_time = (
            edition_time_raw[:2]
            + ":"
            + edition_time_raw[2:]
        )

        try:
            expected = build_edition_id(
                publication_date,
                edition_time,
                language=language,
            )
        except ValueError:
            return False

        return expected == edition_id
