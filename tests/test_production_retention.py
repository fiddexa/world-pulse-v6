import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pipeline.production_retention import (
    cleanup_production_state,
    prune_edition_archives,
    prune_event_memory,
)


def _create_delivery_db(path: Path) -> None:
    db = sqlite3.connect(path)
    db.execute(
        """
        CREATE TABLE edition_delivery_records (
            fingerprint TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.executemany(
        """
        INSERT INTO edition_delivery_records
        (fingerprint, channel, status, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                "old",
                "telegram_newspaper",
                "SENT",
                "2026-08-01 10:00:00",
            ),
            (
                "new",
                "telegram_newspaper",
                "SENT",
                "2026-09-14 10:00:00",
            ),
        ],
    )
    db.commit()
    db.close()


def _create_event_db(path: Path) -> None:
    db = sqlite3.connect(path)

    db.execute(
        """
        CREATE TABLE event_memory (
            fingerprint TEXT PRIMARY KEY,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            occurrence_count INTEGER NOT NULL,
            last_edition_id TEXT
        )
        """
    )

    db.execute(
        """
        CREATE TABLE event_edition_history (
            fingerprint TEXT NOT NULL,
            edition_id TEXT NOT NULL,
            used_at TEXT NOT NULL,
            PRIMARY KEY (fingerprint, edition_id)
        )
        """
    )

    db.executemany(
        """
        INSERT INTO event_memory
        (fingerprint, first_seen, last_seen,
         occurrence_count, last_edition_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                "old-event",
                "2026-07-01 10:00:00",
                "2026-08-01 10:00:00",
                5,
                "AROUND-THE-MAIN-EN-2026-08-01-0700",
            ),
            (
                "new-event",
                "2026-09-10 10:00:00",
                "2026-09-14 10:00:00",
                2,
                "AROUND-THE-MAIN-EN-2026-09-14-0700",
            ),
        ],
    )

    db.executemany(
        """
        INSERT INTO event_edition_history
        (fingerprint, edition_id, used_at)
        VALUES (?, ?, ?)
        """,
        [
            (
                "old-event",
                "AROUND-THE-MAIN-EN-2026-08-01-0700",
                "2026-08-01 10:00:00",
            ),
            (
                "new-event",
                "AROUND-THE-MAIN-EN-2026-09-14-0700",
                "2026-09-14 10:00:00",
            ),
        ],
    )

    db.commit()
    db.close()


def test_prune_edition_archives_keeps_latest_12(tmp_path):
    root = tmp_path / "editions"
    root.mkdir()

    for day in range(1, 16):
        name = (
            f"AROUND-THE-MAIN-EN-2026-09-"
            f"{day:02d}-0700.json"
        )
        (root / name).write_text(
            json.dumps({"edition": day}),
            encoding="utf-8",
        )

    removed = prune_edition_archives(
        archive_root=root,
        keep=12,
    )

    remaining = sorted(path.name for path in root.glob("*.json"))

    assert len(removed) == 3
    assert len(remaining) == 12
    assert remaining == [
        f"AROUND-THE-MAIN-EN-2026-09-{day:02d}-0700.json"
        for day in range(4, 16)
    ]


def test_prune_event_memory_removes_old_event_and_history(tmp_path):
    db_path = tmp_path / "event_memory.sqlite3"
    _create_event_db(db_path)

    deleted_events, deleted_history = prune_event_memory(
        db_path=db_path,
        retention_days=30,
        now=datetime(
            2026,
            9,
            15,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert deleted_events == 1
    assert deleted_history == 1

    db = sqlite3.connect(db_path)

    assert db.execute(
        "SELECT COUNT(*) FROM event_memory"
    ).fetchone()[0] == 1

    assert db.execute(
        "SELECT COUNT(*) FROM event_edition_history"
    ).fetchone()[0] == 1

    db.close()


def test_cleanup_production_state(tmp_path):
    archive_root = tmp_path / "editions"
    archive_root.mkdir()

    for number in range(1, 15):
        (archive_root / (
            f"AROUND-THE-MAIN-EN-2026-09-"
            f"{number:02d}-0700.json"
        )).write_text(
            "{}",
            encoding="utf-8",
        )

    delivery_db = tmp_path / "edition_delivery.sqlite3"
    event_db = tmp_path / "event_memory.sqlite3"

    _create_delivery_db(delivery_db)
    _create_event_db(event_db)

    result = cleanup_production_state(
        now=datetime(
            2026,
            9,
            15,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        archive_root=archive_root,
        delivery_db=delivery_db,
        event_memory_db=event_db,
    )

    assert len(result["removed_archives"]) == 2
    assert result["deleted_delivery_rows"] == 1
    assert result["deleted_event_memory_rows"] == 1
    assert result["deleted_event_history_rows"] == 1
