from datetime import datetime
from zoneinfo import ZoneInfo

from pipeline.mobile_telegram_production import (
    get_due_edition_slots,
)


TZ = ZoneInfo("America/New_York")


def test_watchdog_returns_due_slots_in_order():
    now = datetime(
        2026,
        9,
        16,
        13,
        30,
        tzinfo=TZ,
    )

    slots = get_due_edition_slots(now)

    assert [
        (item["edition_date"], item["edition_time"])
        for item in slots
    ] == [
        ("2026-09-16", "07:00"),
        ("2026-09-16", "13:00"),
    ]


def test_watchdog_does_not_return_future_slot():
    now = datetime(
        2026,
        9,
        16,
        12,
        30,
        tzinfo=TZ,
    )

    slots = get_due_edition_slots(now)

    assert [
        item["edition_time"]
        for item in slots
    ] == ["07:00"]


def test_watchdog_keeps_previous_evening_slot_when_needed():
    now = datetime(
        2026,
        9,
        17,
        6,
        30,
        tzinfo=TZ,
    )

    slots = get_due_edition_slots(now)

    assert [
        (item["edition_date"], item["edition_time"])
        for item in slots
    ] == [
        ("2026-09-16", "20:00"),
    ]


def test_watchdog_processes_all_due_slots_in_order(monkeypatch):
    from pipeline.mobile_telegram_production import (
        run_mobile_telegram_watchdog,
    )

    now = datetime(
        2026,
        9,
        16,
        20,
        30,
        tzinfo=TZ,
    )

    processed = []

    def fake_release(*, current_time=None, resolved=None, **kwargs):
        processed.append(
            (
                resolved["edition_date"],
                resolved["edition_time"],
            )
        )
        return {
            "status": "SENT",
            "edition_id": resolved["edition_id"],
        }

    monkeypatch.setattr(
        "pipeline.mobile_telegram_production.run_mobile_telegram_release",
        fake_release,
    )

    result = run_mobile_telegram_watchdog(
        current_time=now,
    )

    assert processed == [
        ("2026-09-16", "07:00"),
        ("2026-09-16", "13:00"),
        ("2026-09-16", "20:00"),
    ]

    assert result["status"] == "COMPLETED"
    assert result["sent"] == 3


def test_watchdog_second_run_does_not_duplicate_sent_slots(monkeypatch):
    from pipeline.mobile_telegram_production import (
        run_mobile_telegram_watchdog,
    )

    now = datetime(
        2026,
        9,
        16,
        13,
        30,
        tzinfo=TZ,
    )

    sent = set()
    calls = []

    def fake_already_sent(edition_id):
        return edition_id in sent

    def fake_release(*, current_time=None, resolved=None, **kwargs):
        edition_id = resolved["edition_id"]

        calls.append(edition_id)

        sent.add(edition_id)

        return {
            "status": "SENT",
            "edition_id": edition_id,
        }

    monkeypatch.setattr(
        "pipeline.mobile_telegram_production.newspaper_delivery_already_sent",
        fake_already_sent,
    )

    monkeypatch.setattr(
        "pipeline.mobile_telegram_production.run_mobile_telegram_release",
        fake_release,
    )

    first = run_mobile_telegram_watchdog(
        current_time=now,
    )

    second = run_mobile_telegram_watchdog(
        current_time=now,
    )

    assert first["status"] == "COMPLETED"
    assert second["status"] == "COMPLETED"

    assert calls == [
        "AROUND-THE-MAIN-EN-2026-09-16-0700",
        "AROUND-THE-MAIN-EN-2026-09-16-1300",
    ]


def test_watchdog_stops_after_failed_slot_and_retries_later(monkeypatch):
    from pipeline.mobile_telegram_production import (
        run_mobile_telegram_watchdog,
    )

    now = datetime(
        2026,
        9,
        16,
        13,
        30,
        tzinfo=TZ,
    )

    calls = []

    def fake_release(*, current_time=None, resolved=None, **kwargs):
        edition_id = resolved["edition_id"]
        calls.append(edition_id)

        if resolved["edition_time"] == "07:00":
            return {
                "status": "FAILED",
                "edition_id": edition_id,
                "reason": "TEMPORARY_FAILURE",
            }

        return {
            "status": "SENT",
            "edition_id": edition_id,
        }

    monkeypatch.setattr(
        "pipeline.mobile_telegram_production.run_mobile_telegram_release",
        fake_release,
    )

    first = run_mobile_telegram_watchdog(
        current_time=now,
    )

    assert first["status"] == "FAILED"

    assert calls == [
        "AROUND-THE-MAIN-EN-2026-09-16-0700",
    ]

    calls.clear()

    def retry_release(*, current_time=None, resolved=None, **kwargs):
        edition_id = resolved["edition_id"]
        calls.append(edition_id)

        return {
            "status": "SENT",
            "edition_id": edition_id,
        }

    monkeypatch.setattr(
        "pipeline.mobile_telegram_production.run_mobile_telegram_release",
        retry_release,
    )

    second = run_mobile_telegram_watchdog(
        current_time=now,
    )

    assert second["status"] == "COMPLETED"

    assert calls == [
        "AROUND-THE-MAIN-EN-2026-09-16-0700",
        "AROUND-THE-MAIN-EN-2026-09-16-1300",
    ]


def test_watchdog_catches_up_multiple_missed_slots(monkeypatch):
    from pipeline.mobile_telegram_production import (
        run_mobile_telegram_watchdog,
    )

    now = datetime(
        2026,
        9,
        16,
        13,
        30,
        tzinfo=TZ,
    )

    calls = []

    def fake_release(*, current_time=None, resolved=None, **kwargs):
        calls.append(resolved["edition_id"])

        return {
            "status": "SENT",
            "edition_id": resolved["edition_id"],
        }

    monkeypatch.setattr(
        "pipeline.mobile_telegram_production.run_mobile_telegram_release",
        fake_release,
    )

    result = run_mobile_telegram_watchdog(
        current_time=now,
    )

    assert result["status"] == "COMPLETED"
    assert result["sent"] == 2
    assert result["failed"] == 0

    assert calls == [
        "AROUND-THE-MAIN-EN-2026-09-16-0700",
        "AROUND-THE-MAIN-EN-2026-09-16-1300",
    ]
