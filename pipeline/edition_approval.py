"""Approval-manifest access for AROUND THE MAIN edition publication."""

from __future__ import annotations

import json
from pathlib import Path


APPROVAL_PENDING = "PENDING"
APPROVAL_APPROVED = "APPROVED"
APPROVAL_REJECTED = "REJECTED"


def get_edition_approval_status(
    edition_id,
    approval_manifest_path: str | Path | None,
) -> str | None:
    """Return the exact status for this edition's approval manifest.

    ``None`` means that no usable approval record exists.  A manifest for a
    different edition is deliberately not an approval record for the caller.
    Status values are returned without normalization: publication requires the
    manifest value to be exactly ``APPROVED``.
    """
    expected_edition_id = str(edition_id or "").strip()

    if not expected_edition_id or approval_manifest_path is None:
        return None

    try:
        manifest_path = Path(approval_manifest_path)

        if not manifest_path.is_file():
            return None

        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(manifest, dict):
        return None

    manifest_edition_id = str(
        manifest.get("edition_id") or ""
    ).strip()

    if manifest_edition_id != expected_edition_id:
        return None

    status = manifest.get("approval_status")

    return status if isinstance(status, str) else None
