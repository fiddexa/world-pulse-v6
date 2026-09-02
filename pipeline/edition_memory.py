"""
AROUND THE MAIN v6 - Persistent Edition Memory

Stores persistent execution state for AROUND THE MAIN editions.

Edition identity is based on the stable Edition ID.

This layer is responsible only for edition-level execution state.
It does not build editions and does not publish externally.
"""

import sqlite3
from pathlib import Path
from typing import Any


RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"


VALID_STATUSES = {
    RUNNING,
    COMPLETED,
    FAILED,
}


class EditionMemory:
    """
    Persistent SQLite memory for edition execution state.

    Each Edition ID has one persistent state.
    """

    def __init__(
        self,
        db_path: str | Path = "data/edition_memory.sqlite3",
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
            CREATE TABLE IF NOT EXISTS edition_memory (
                edition_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
            """
        )

        self._connection.commit()

    @staticmethod
    def _valid_edition_id(
        edition_id: Any,
    ) -> bool:
        return (
            isinstance(edition_id, str)
            and bool(edition_id.strip())
        )

    @staticmethod
    def _valid_status(
        status: Any,
    ) -> bool:
        return status in VALID_STATUSES

    def status(
        self,
        edition_id: Any,
    ) -> str | None:
        """
        Return the current status of an edition.
        """

        if not self._valid_edition_id(edition_id):
            return None

        row = self._connection.execute(
            """
            SELECT status
            FROM edition_memory
            WHERE edition_id = ?
            """,
            (edition_id.strip(),),
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def exists(
        self,
        edition_id: Any,
    ) -> bool:
        """
        Return True when an edition has a stored state.
        """

        return self.status(edition_id) is not None

    def start(
        self,
        edition_id: Any,
    ) -> bool:
        """
        Mark an edition as RUNNING.

        Returns False when the edition already has a state.
        """

        if not self._valid_edition_id(edition_id):
            return False

        edition_id = edition_id.strip()

        try:
            self._connection.execute(
                """
                INSERT INTO edition_memory (
                    edition_id,
                    status,
                    created_at,
                    completed_at
                )
                VALUES (
                    ?,
                    ?,
                    CURRENT_TIMESTAMP,
                    NULL
                )
                """,
                (
                    edition_id,
                    RUNNING,
                ),
            )

            self._connection.commit()

        except sqlite3.IntegrityError:
            return False

        return True

    def complete(
        self,
        edition_id: Any,
    ) -> bool:
        """
        Mark an existing edition as COMPLETED.
        """

        if not self._valid_edition_id(edition_id):
            return False

        cursor = self._connection.execute(
            """
            UPDATE edition_memory
            SET
                status = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE edition_id = ?
            """,
            (
                COMPLETED,
                edition_id.strip(),
            ),
        )

        self._connection.commit()

        return cursor.rowcount > 0

    def fail(
        self,
        edition_id: Any,
    ) -> bool:
        """
        Mark an existing edition as FAILED.
        """

        if not self._valid_edition_id(edition_id):
            return False

        cursor = self._connection.execute(
            """
            UPDATE edition_memory
            SET
                status = ?,
                completed_at = NULL
            WHERE edition_id = ?
            """,
            (
                FAILED,
                edition_id.strip(),
            ),
        )

        self._connection.commit()

        return cursor.rowcount > 0

    def can_start(
        self,
        edition_id: Any,
    ) -> bool:
        """
        Return True when the edition has never been started.
        """

        return self.status(edition_id) is None

    def clear(self) -> None:
        """
        Remove all edition execution records.
        """

        self._connection.execute(
            "DELETE FROM edition_memory"
        )

        self._connection.commit()

    def close(self) -> None:
        """
        Close the SQLite connection.
        """

        self._connection.close()
