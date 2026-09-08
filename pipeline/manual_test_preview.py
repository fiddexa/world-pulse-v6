from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline.production_job import collect_production_articles
from pipeline.production_job import run_test_production_job
from pipeline.edition_memory import EditionMemory
from pipeline.event_memory import EventMemory
from pipeline.edition_preview import build_edition_preview


OUTPUT_ROOT = Path("data/previews/manual-test")


def main():
    print("=" * 70)
    print("AROUND THE MAIN — MANUAL REAL NEWS PREVIEW")
    print("=" * 70)

    articles = collect_production_articles(timeout=20)

    print(f"\nCollected articles: {len(articles)}")

    if not articles:
        print("ERROR: No articles collected.")
        return

    now = datetime.now(ZoneInfo("Asia/Tashkent"))

    print("Test time:", now.isoformat())

    result = run_test_production_job(
        publication_date=now.date(),
        edition_time=now.strftime("%H:%M"),
        timeout=20,
        language="en",
        event_memory=EventMemory(),
    )

    print("\nScheduler status:", result.get("status"))
    print("Edition:", result.get("edition_label"))
    print("Edition ID:", result.get("edition_id"))

    edition = result.get("edition")

    if not isinstance(edition, dict):
        print("\nEDITION NOT CREATED.")
        print("Reason:", result.get("reason"))
        return

    print("\nEdition created successfully.")
    print("Event count:", edition.get("event_count"))
    print("Main stories:", len(edition.get("main_stories", [])))
    print("Briefs:", len(edition.get("briefs", [])))
    print("Sections:", len(edition.get("sections", [])))

    edition_id = edition.get("edition_id", "manual-edition")
    output = OUTPUT_ROOT / str(edition_id)

    preview = build_edition_preview(
        edition,
        output,
    )

    print("\n" + "=" * 70)
    print("PREVIEW CREATED")
    print("=" * 70)

    print("Edition:", preview.get("edition_label"))
    print("Status:", preview.get("approval_status"))
    print("Preview:", preview.get("preview_root"))
    print("Manifest:", preview.get("manifest_path"))

    print("\nFULL EDITION:")

    for path in preview["full_edition"]["files"]:
        print(" ", path)

    print("\nMOBILE EDITION:")
    print(" ", preview["mobile_edition"]["file"])

    print("\nPUBLISH: NOT EXECUTED")
    print("=" * 70)


if __name__ == "__main__":
    main()
