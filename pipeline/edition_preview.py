from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.edition_rendering import render_edition


APPROVAL_PENDING = "PENDING"
APPROVAL_APPROVED = "APPROVED"
APPROVAL_REJECTED = "REJECTED"


def build_edition_preview(
    edition: dict[str, Any],
    output_root: str | Path,
) -> dict[str, Any]:
    """
    Build a visual preview package for ONE edition.

    This function:
      - renders FULL EDITION;
      - renders MOBILE EDITION;
      - writes a manifest;
      - marks the preview as PENDING.

    It does NOT publish anything.
    It does NOT call Telegram.
    It does NOT allocate an edition number.
    """

    if not isinstance(edition, dict):
        raise ValueError(
            "edition must be a dictionary"
        )

    root = Path(output_root)
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    rendered = render_edition(
        edition,
        root,
    )

    manifest = {
        "edition_id": edition.get(
            "edition_id"
        ),
        "edition_year": edition.get(
            "edition_year"
        ),
        "edition_number": edition.get(
            "edition_number"
        ),
        "edition_label": edition.get(
            "edition_label"
        ),
        "approval_status": APPROVAL_PENDING,
        "full_edition": rendered.get(
            "full_edition",
            {},
        ),
        "mobile_edition": rendered.get(
            "mobile_edition",
            {},
        ),
    }

    manifest_path = root / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        **manifest,
        "preview_root": str(root),
        "manifest_path": str(
            manifest_path
        ),
    }


def approve_edition_preview(
    preview_root: str | Path,
) -> dict[str, Any]:
    """
    Approve an existing preview package.

    This changes only the preview manifest.
    It does NOT publish the edition.
    """

    root = Path(preview_root)
    manifest_path = root / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Preview manifest not found: {manifest_path}"
        )

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(manifest, dict):
        raise ValueError(
            "Preview manifest must be a dictionary"
        )

    manifest["approval_status"] = (
        APPROVAL_APPROVED
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return manifest


def reject_edition_preview(
    preview_root: str | Path,
) -> dict[str, Any]:
    """
    Reject an existing preview package.

    This changes only the preview manifest.
    It does NOT publish the edition.
    """

    root = Path(preview_root)
    manifest_path = root / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Preview manifest not found: {manifest_path}"
        )

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(manifest, dict):
        raise ValueError(
            "Preview manifest must be a dictionary"
        )

    manifest["approval_status"] = (
        APPROVAL_REJECTED
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return manifest
