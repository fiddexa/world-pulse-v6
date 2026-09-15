"""
AROUND THE MAIN v6 - Production State Retention

Keeps the persistent production state small while preserving enough
history for resume, deduplication and delivery idempotency.

Policy:
- keep the latest 12 edition archives;
- keep Telegram edition-delivery records for 30 days;
- keep event-memory records seen within the last 30 days;
- keep edition_counter.json untouched.

This module is intended to run only after a successful Telegram
publication.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_EDITION_ARCHIVE_ROOT = Path("data/editions")
DEFAULT_EDITION_DELIVERY_DB = Path("data/edition_delivery.sqlite3")
DEFAULT_EVENT_MEMORY_DB = Path("data/event_memory.sqlite3")

DEFAULT_KEEP_EDITIONS = 12
DEFAULT_DELIVERY_RETENTION_DAYS = 30
DEFAULT_EVENT_RETENTION_DAYS = 30


def _cutoff(days: int, now: datetime | None = None) -> str:
    if days < 0:
        raise ValueError("days must be >= 0")

    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    return (now - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def prune_edition_archives(
    *,
    archive_root: str | Path = DEFAULT_EDITION_ARCHIVE_ROOT,
    keep: int = DEFAULT_KEEP_EDITIONS,
) -> list[Path]:
    """
    Keep the newest `keep` JSON edition archives.

    Edition filenames are canonical and therefore lexicographically
    sortable by publication date/time.
    """
    if keep < 1:
        raise ValueError("keep must be >= 1")

    root = Path(archive_root)

    if not root.exists():
        return []

    archives = sorted(
        root.glob("AROUND-THE-MAIN-*.json"),
        key=lambda path: path.name,
        reverse=True,
    )

    removed: list[Path] = []

    for path in archives[keep:]:
        path.unlink()
        removed.append(path)

    return removed


def prune_delivery_log(
    *,
    db_path: str | Path = DEFAULT_EDITION_DELIVERY_DB,
    retention_days: int = DEFAULT_DELIVERY_RETENTION_DAYS,
    now: datetime | None = None,
) -> int:
    """
    Remove old edition-delivery records.

    Returns the number of deleted rows.
    """
    db = sqlite3.connect(str(db_path))

    try:
        cutoff = _cutoff(
            retention_days,
            now=now,
        )

        cursor = db.execute(
            """
            DELETE FROM edition_delivery_records
            WHERE updated_at < ?
            """,
            (cutoff,),
        )

        db.commit()
        return int(cursor.rowcount)
    finally:
        db.close()


def prune_event_memory(
    *,
    db_path: str | Path = DEFAULT_EVENT_MEMORY_DB,
    retention_days: int = DEFAULT_EVENT_RETENTION_DAYS,
    now: datetime | None = None,
) -> tuple[int, int]:
    """
    Remove event-memory records that have not been seen recently.

    History rows belonging to removed events are deleted first.
    Returns:
        (deleted_event_memory_rows, deleted_history_rows)
    """
    db = sqlite3.connect(str(db_path))

    try:
        cutoff = _cutoff(
            retention_days,
            now=now,
        )

        fingerprints = [
            row[0]
            for row in db.execute(
                """
                SELECT fingerprint
                FROM event_memory
                WHERE last_seen < ?
                """,
                (cutoff,),
            ).fetchall()
        ]

        if not fingerprints:
            return (0, 0)

        placeholders = ",".join(
            "?" for _ in fingerprints
        )

        history_cursor = db.execute(
            f"""
            DELETE FROM event_edition_history
            WHERE fingerprint IN ({placeholders})
            """,
            fingerprints,
        )

        event_cursor = db.execute(
            f"""
            DELETE FROM event_memory
            WHERE fingerprint IN ({placeholders})
            """,
            fingerprints,
        )

        db.commit()

        return (
            int(event_cursor.rowcount),
            int(history_cursor.rowcount),
        )
    finally:
        db.close()


def cleanup_production_state(
    *,
    now: datetime | None = None,
    archive_root: str | Path = DEFAULT_EDITION_ARCHIVE_ROOT,
    delivery_db: str | Path = DEFAULT_EDITION_DELIVERY_DB,
    event_memory_db: str | Path = DEFAULT_EVENT_MEMORY_DB,
    keep_editions: int = DEFAULT_KEEP_EDITIONS,
    delivery_retention_days: int = DEFAULT_DELIVERY_RETENTION_DAYS,
    event_retention_days: int = DEFAULT_EVENT_RETENTION_DAYS,
) -> dict:
    """
    Apply all production retention rules.

    The edition counter is deliberately untouched.
    """
    removed_archives = prune_edition_archives(
        archive_root=archive_root,
        keep=keep_editions,
    )

    deleted_delivery = prune_delivery_log(
        db_path=delivery_db,
        retention_days=delivery_retention_days,
        now=now,
    )

    deleted_events, deleted_history = prune_event_memory(
        db_path=event_memory_db,
        retention_days=event_retention_days,
        now=now,
    )

    return {
        "removed_archives": [
            str(path)
            for path in removed_archives
        ],
        "deleted_delivery_rows": deleted_delivery,
        "deleted_event_memory_rows": deleted_events,
        "deleted_event_history_rows": deleted_history,
        "keep_editions": keep_editions,
        "delivery_retention_days": delivery_retention_days,
        "event_retention_days": event_retention_days,
    }
