"""
AROUND THE MAIN - Mobile-only autonomous Telegram production.

Production path:
COLLECT -> EDITORIAL -> MOBILE -> APPROVAL/QC -> TELEGRAM

Audio is intentionally excluded from this production path.
Full Edition is intentionally excluded from this production path.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline.edition_approval import (
    APPROVAL_APPROVED,
    get_edition_approval_status,
)
from pipeline.edition_id import DEFAULT_TIMEZONE
from pipeline.edition_memory import (
    COMPLETED,
    RUNNING,
    EditionMemory,
)
from pipeline.production_retention import (
    cleanup_production_state,
)
from pipeline.edition_preview import approve_edition_preview
from pipeline.edition_slot_resolver import resolve_edition_slot
from pipeline.mobile_renderer import render_mobile_edition
from pipeline.market_data import fetch_market_snapshot
from pipeline.production_job import run_production_job
from pipeline.telegram_newspaper_runner import (
    _telegram_send_photo,
    newspaper_delivery_already_sent,
    publish_edition_newspaper_to_telegram,
)


TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE)

DATA_ROOT = Path("data")
EDITION_ARCHIVE_ROOT = DATA_ROOT / "editions"
MOBILE_OUTPUT_ROOT = DATA_ROOT / "newspaper"
APPROVAL_ROOT = DATA_ROOT / "previews" / "mobile-production"

POLL_SECONDS = 30
MAX_CATCHUP_HOURS = 4

TELEGRAM_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ENV = "TELEGRAM_CHAT_ID"


def _safe_id(value: str) -> str:
    return (
        re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            str(value or ""),
        )
        .strip("._")
        or "edition"
    )


def _now() -> datetime:
    return datetime.now(TIMEZONE)


def _edition_slot_datetime(resolved: dict) -> datetime:
    return datetime.fromisoformat(
        f'{resolved["edition_date"]}T{resolved["edition_time"]}'
    ).replace(tzinfo=TIMEZONE)


def _edition_json_path(edition_id: str) -> Path:
    return (
        EDITION_ARCHIVE_ROOT
        / f"{_safe_id(edition_id)}.json"
    )


def _mobile_root(edition_id: str) -> Path:
    return (
        MOBILE_OUTPUT_ROOT
        / _safe_id(edition_id)
        / "mobile"
    )


def _approval_dir(edition_id: str) -> Path:
    return (
        APPROVAL_ROOT
        / _safe_id(edition_id)
    )


def _approval_manifest(edition_id: str) -> Path:
    return (
        _approval_dir(edition_id)
        / "manifest.json"
    )


def _save_edition(edition: dict) -> Path:
    EDITION_ARCHIVE_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    edition_id = str(
        edition.get("edition_id") or ""
    ).strip()

    path = _edition_json_path(edition_id)

    path.write_text(
        json.dumps(
            edition,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def _load_saved_edition(edition_id: str) -> dict | None:
    path = _edition_json_path(edition_id)

    if not path.is_file():
        return None

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None

    return value if isinstance(value, dict) else None


def _write_pending_manifest(
    edition: dict,
    pages: list[Path],
    mobile_root: Path,
) -> Path:
    edition_id = str(
        edition.get("edition_id") or ""
    ).strip()

    approval_dir = _approval_dir(edition_id)
    approval_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "edition_id": edition_id,
        "edition_year": int(
            edition.get("edition_year") or 0
        ),
        "edition_number": int(
            edition.get("edition_number") or 0
        ),
        "edition_label": str(
            edition.get("edition_label") or ""
        ),
        "event_count": len(
            (
                edition.get("mobile_audio") or {}
            ).get("events") or []
        ),
        "approval_status": "PENDING",
        "full_edition": {
            "source": "NOT_RENDERED_MOBILE_ONLY"
        },
        "mobile_edition": {
            "source": str(mobile_root),
            "file": str(
                mobile_root / "mobile.png"
            ),
            "pages": [
                str(path)
                for path in pages
            ],
        },
    }

    path = _approval_manifest(edition_id)

    path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def _retry_photo_transport(
    *,
    chat_id,
    photo_path,
    caption="",
):
    max_attempts = 6

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        response = _telegram_send_photo(
            chat_id=chat_id,
            photo_path=photo_path,
            caption=caption,
        )

        if (
            isinstance(response, dict)
            and response.get("ok") is True
        ):
            return response

        retry_after = None

        if isinstance(response, dict):
            raw = response.get("response")

            if isinstance(raw, str):
                try:
                    payload = json.loads(raw)
                    retry_after = (
                        payload
                        .get("parameters", {})
                        .get("retry_after")
                    )
                except Exception:
                    retry_after = None

        if retry_after is not None:
            wait_seconds = (
                int(retry_after) + 2
            )

            print(
                "Telegram 429:",
                f"waiting {wait_seconds}s",
                f"(attempt {attempt}/{max_attempts})",
            )

            time.sleep(wait_seconds)
            continue

        return response

    return {
        "ok": False,
        "error": (
            "TELEGRAM_RETRY_LIMIT_EXCEEDED"
        ),
    }


def run_mobile_telegram_release(
    *,
    current_time: datetime | None = None,
    language: str = "en",
    timeout: int = 20,
    dry_run: bool = False,
) -> dict:
    """
    Run one Mobile-only production release.

    Audio is never generated.
    Full Edition is never rendered.
    """

    current_time = (
        current_time
        if current_time is not None
        else _now()
    )

    resolved = resolve_edition_slot(
        current_time,
        language=language,
    )

    edition_id = resolved["edition_id"]

    slot_time = _edition_slot_datetime(
        resolved
    )

    age_hours = (
        current_time.astimezone(TIMEZONE)
        - slot_time
    ).total_seconds() / 3600

    if age_hours < 0:
        return {
            "status": "SKIPPED",
            "edition_id": edition_id,
            "reason": "SLOT_NOT_ACTIVE",
        }

    if age_hours > MAX_CATCHUP_HOURS:
        return {
            "status": "SKIPPED",
            "edition_id": edition_id,
            "reason": "SLOT_TOO_OLD",
        }

    memory = EditionMemory()
    state = memory.status(edition_id)

    if newspaper_delivery_already_sent(
        edition_id
    ):
        return {
            "status": "SKIPPED",
            "edition_id": edition_id,
            "reason": "ALREADY_SENT",
        }

    print(
        "=== MOBILE PRODUCTION ==="
    )
    print("EDITION ID:", edition_id)
    print(
        "DATE:",
        resolved["edition_date"],
    )
    print(
        "TIME:",
        resolved["edition_time"],
    )
    print(
        "MEMORY STATUS:",
        state,
    )

    if state == RUNNING:
        return {
            "status": "SKIPPED",
            "edition_id": edition_id,
            "reason": "EDITION_RUNNING",
        }

    edition = _load_saved_edition(
        edition_id
    )

    if edition is None:
        if state == COMPLETED:
            return {
                "status": "FAILED",
                "edition_id": edition_id,
                "reason": (
                    "COMPLETED_EDITION_ARCHIVE_MISSING"
                ),
            }

        if dry_run:
            return {
                "status": "DRY_RUN",
                "edition_id": edition_id,
                "reason": "WOULD_RUN_PRODUCTION",
            }

        production = run_production_job(
            current_time=current_time,
            language=language,
            timeout=timeout,
        )

        if production.get("status") != "COMPLETED":
            return production

        edition = production.get("edition")

        if not isinstance(
            edition,
            dict,
        ):
            return {
                "status": "FAILED",
                "edition_id": edition_id,
                "reason": "EDITION_NOT_RETURNED",
            }

        edition["publication_date"] = (
            production["edition_date"]
        )
        edition["edition_time"] = (
            production["edition_time"]
        )
        edition["edition_year"] = (
            production["edition_year"]
        )
        edition["edition_number"] = (
            production["edition_number"]
        )
        edition["edition_label"] = (
            production["edition_label"]
        )

        market_snapshot = fetch_market_snapshot(
            timeout=15,
        )

        edition["market_snapshot"] = (
            market_snapshot
        )

        print(
            "MARKET SNAPSHOT:",
            market_snapshot.get("provider"),
        )
        print(
            "MARKET FETCHED AT:",
            market_snapshot.get("fetched_at"),
        )
        print(
            "MARKET QUOTES:",
            len(
                market_snapshot.get("quotes") or {}
            ),
        )

        archive_path = _save_edition(
            edition
        )

        print(
            "EDITION ARCHIVED:",
            archive_path,
        )

    mobile_root = _mobile_root(
        edition_id
    )

    mobile_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = sorted(
        mobile_root.glob("page-*.png")
    )

    if not pages:
        if dry_run:
            return {
                "status": "DRY_RUN",
                "edition_id": edition_id,
                "reason": "WOULD_RENDER_MOBILE",
            }

        render_mobile_edition(
            edition,
            mobile_root / "mobile.png",
        )

        pages = sorted(
            mobile_root.glob("page-*.png")
        )

    if not pages:
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "NO_MOBILE_PAGES",
        }

    if not all(
        page.is_file()
        and page.stat().st_size > 0
        for page in pages
    ):
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "INVALID_MOBILE_PAGE",
        }

    manifest_path = _approval_manifest(
        edition_id
    )

    if not manifest_path.is_file():
        if dry_run:
            return {
                "status": "DRY_RUN",
                "edition_id": edition_id,
                "reason": "WOULD_APPROVE_MOBILE",
            }

        _write_pending_manifest(
            edition,
            pages,
            mobile_root,
        )

        approve_edition_preview(
            _approval_dir(edition_id)
        )

    approval = get_edition_approval_status(
        edition_id,
        manifest_path,
    )

    if approval != APPROVAL_APPROVED:
        return {
            "status": "FAILED",
            "edition_id": edition_id,
            "reason": "APPROVAL_NOT_APPROVED",
            "approval_status": approval,
        }

    if dry_run:
        return {
            "status": "DRY_RUN",
            "edition_id": edition_id,
            "edition_number": edition.get(
                "edition_number"
            ),
            "page_count": len(pages),
            "approval_status": approval,
        }

    token = os.getenv(
        TELEGRAM_TOKEN_ENV,
        "",
    ).strip()

    chat_id = os.getenv(
        TELEGRAM_CHAT_ENV,
        "",
    ).strip()

    if not token or not chat_id:
        return {
            "status": "NOT_CONFIGURED",
            "edition_id": edition_id,
        }

    delivery = publish_edition_newspaper_to_telegram(
        edition_id,
        pages,
        edition_number=edition.get(
            "edition_number"
        ),
        approval_manifest_path=manifest_path,
        transport=_retry_photo_transport,
        chat_id=chat_id,
    )

    if delivery.get("status") == "SENT":
        retention = cleanup_production_state()
        print(
            "PRODUCTION RETENTION:",
            retention,
        )

    return {
        "status": delivery.get(
            "status",
            "FAILED",
        ),
        "edition_id": edition_id,
        "edition_number": edition.get(
            "edition_number"
        ),
        "page_count": len(pages),
        "delivery": delivery,
    }


def run_forever(
    *,
    poll_seconds: int = POLL_SECONDS,
) -> None:
    """
    Persistent hosted scheduler.

    The host must provide persistent storage for the data/ directory.
    """

    print(
        "AROUND THE MAIN Mobile-only scheduler started"
    )
    print(
        "Timezone:",
        DEFAULT_TIMEZONE,
    )
    print(
        "Slots: 07:00 / 13:00 / 20:00"
    )
    print(
        "Audio: DISABLED"
    )
    print(
        "Full Edition: DISABLED"
    )

    while True:
        try:
            result = (
                run_mobile_telegram_release()
            )

            if result.get("status") not in {
                "SKIPPED",
            }:
                print(
                    "RELEASE RESULT:",
                    result,
                )

        except Exception as exc:
            print(
                "SCHEDULER ERROR:",
                repr(exc),
            )

        time.sleep(
            max(
                10,
                int(poll_seconds),
            )
        )


if __name__ == "__main__":
    run_forever()
