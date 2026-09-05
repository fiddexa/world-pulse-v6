from pathlib import Path
import json

from pipeline.production_job import run_test_production_job
from pipeline.edition_preview import (
    build_edition_preview,
    approve_edition_preview,
)
from pipeline.edition_publication import build_edition_publication
from pipeline.edition_telegram_runner import publish_edition_to_telegram


PUBLICATION_DATE = "2026-09-05"
EDITION_TIME = "22:00"

PREVIEW_ROOT = (
    Path("data/previews")
    / f"manual-edition-{PUBLICATION_DATE}-{EDITION_TIME.replace(':', '')}"
)


def main():
    print("=" * 70)
    print("AROUND THE MAIN — MANUAL TEXT PUBLICATION TEST")
    print("=" * 70)

    result = run_test_production_job(
        publication_date=PUBLICATION_DATE,
        edition_time=EDITION_TIME,
    )

    print()
    print("PRODUCTION STATUS:", result.get("status"))
    print("EDITION:", result.get("edition_label"))
    print("EDITION ID:", result.get("edition_id"))

    if result.get("status") != "COMPLETED":
        print()
        print("EDITION CREATION FAILED")
        print(result)
        return

    edition = result.get("edition")

    if not isinstance(edition, dict):
        print()
        print("EDITION NOT CREATED")
        return

    print()
    print("MAIN STORIES:", len(edition.get("main_stories", [])))
    print("BRIEFS:", len(edition.get("briefs", [])))
    print("EVENT COUNT:", edition.get("event_count"))

    print()
    print("BUILDING PREVIEW...")

    preview = build_edition_preview(
        edition,
        PREVIEW_ROOT,
    )

    print("PREVIEW:", preview.get("preview_root"))
    print("MANIFEST:", preview.get("manifest_path"))
    print("APPROVAL:", preview.get("approval_status"))

    approved = approve_edition_preview(
        PREVIEW_ROOT
    )

    manifest_path = approved.get("manifest_path")

    print()
    print("APPROVAL AFTER CONFIRMATION:")
    print(approved.get("approval_status"))
    print("MANIFEST PATH:", manifest_path)

    if not manifest_path:
        print()
        print("ERROR: APPROVAL MANIFEST PATH IS MISSING")
        return

    print()
    print("BUILDING TELEGRAM TEXT PACKAGE...")

    publication = build_edition_publication(
        edition
    )

    if not isinstance(publication, dict):
        print("ERROR: PUBLICATION PACKAGE WAS NOT CREATED")
        return

    print(
        "PUBLICATION EDITION ID:",
        publication.get("edition_id"),
    )

    print()
    print("PUBLISHING TEXT TO TELEGRAM...")

    delivery = publish_edition_to_telegram(
        publication,
        approval_manifest_path=manifest_path,
    )

    print()
    print("=" * 70)
    print("TELEGRAM TEXT PUBLICATION RESULT")
    print("=" * 70)

    print(
        json.dumps(
            delivery,
            ensure_ascii=False,
            indent=2,
        )
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
