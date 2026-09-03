from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.edition_pages import build_edition_pages
from pipeline.mobile_renderer import render_mobile_edition
from pipeline.newspaper_renderer import (
    plan_section_pages,
    render_newspaper,
    render_section_page,
)


def render_edition(
    edition: dict[str, Any],
    output_root: str | Path,
) -> dict[str, Any]:
    """
    Render ONE edition into two presentations.

    PAGE 01:
        Existing approved FRONT PAGE renderer.

    PAGE 02+:
        Page-specific section renderer using EditionPage.events.

    MOBILE:
        One vertical feed containing all events from the edition.
    """

    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    root = Path(output_root)

    full_root = root / "full"
    mobile_root = root / "mobile"

    full_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    mobile_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = build_edition_pages(
        edition
    )

    full_files: list[str] = []

    # A preview directory can be reused.  Remove only old generated page
    # images before writing the new manifest, so it can never reference a
    # different set of physical pages than the directory contains.
    for stale_page in full_root.glob("page-*.png"):
        stale_page.unlink()

    physical_page_number = 1

    for page in pages:
        if page.page_number == 1:
            output_path = full_root / "page-01.png"
            render_newspaper(
                edition,
                output_path,
                page_number=physical_page_number,
            )
            full_files.append(str(output_path))
            physical_page_number += 1
        else:
            for plan in plan_section_pages(page):
                output_path = (
                    full_root / f"page-{physical_page_number:02d}.png"
                )
                render_section_page(
                    edition,
                    page,
                    output_path,
                    page_number=physical_page_number,
                    page_plan=plan,
                )
                full_files.append(str(output_path))
                physical_page_number += 1

    mobile_path = (
    mobile_root
    / "mobile.png"
    )

    rendered_mobile = render_mobile_edition(
    edition,
    mobile_path,
    )

    return {
        "edition_id": edition.get(
            "edition_id"
        ),
        "edition_label": edition.get(
            "edition_label"
        ),
        "full_edition": {
            "page_count": len(full_files),
            "files": full_files,
        },
        "mobile_edition": {
    "file": str(mobile_path),
    "pages": [
        str(path)
        for path in sorted(
            mobile_root.glob("page-*.png")
        )
    ],
},
    }
